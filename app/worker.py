import os
import io
import time
import base64
import logging
import threading
from datetime import datetime, timezone, timedelta
import httpx
from google.cloud import firestore as gc_firestore

from app.firebase_client import get_firestore, upload_image_to_storage
from app.processing.cleanup import clean_fabric_image
from app.processing.texture_map import drape_fabric_on_template

logger = logging.getLogger("fabric-engine.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

TEMPLATES_ROOT = os.path.join(os.path.dirname(__file__), "templates")
STALL_TIMEOUT_SECONDS = 180  # 3 minutes
MAX_ATTEMPTS = 3
POLL_INTERVAL_SECONDS = 4

class FabricQueueWorker:
    def __init__(self):
        self._running = False
        self._thread = None
        self.last_poll_at = None
        self.jobs_processed = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="fabric-queue-worker")
        self._thread.start()
        logger.info("FabricQueueWorker background thread started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("FabricQueueWorker stopped.")

    def _run_loop(self):
        logger.info("Entering queue polling loop...")
        while self._running:
            self.last_poll_at = datetime.now(timezone.utc)
            try:
                self._check_stalled_jobs()
                processed_any = self._process_next_job()
                if not processed_any:
                    time.sleep(POLL_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Error in worker polling loop: {e}", exc_info=True)
                time.sleep(POLL_INTERVAL_SECONDS)

    def _check_stalled_jobs(self):
        """
        Finds jobs stuck in 'processing' status longer than STALL_TIMEOUT_SECONDS.
        Resets them to 'queued' or marks as 'failed' if attempts exceeded.
        """
        try:
            db = get_firestore()
            stall_cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALL_TIMEOUT_SECONDS)
            
            # Simple query without composite index requirement
            stalled_docs = db.collection("fabricJobs") \
                .where("status", "==", "processing") \
                .limit(20) \
                .get()

            for doc in stalled_docs:
                data = doc.to_dict()
                started_at = data.get("startedAt")
                if not started_at:
                    continue
                # Handle Firestore DatetimeWithNanoseconds or epoch
                if hasattr(started_at, "timestamp"):
                    started_dt = started_at
                elif isinstance(started_at, (int, float)):
                    started_dt = datetime.fromtimestamp(started_at / 1000.0, timezone.utc)
                else:
                    continue

                if started_dt > stall_cutoff:
                    continue

                attempts = data.get("attempts", 1) + 1
                job_ref = doc.reference
                logger.warning(f"Job {doc.id} stalled (started > 3m ago). Attempt #{attempts}")
                
                if attempts >= MAX_ATTEMPTS:
                    job_ref.update({
                        "status": "failed",
                        "attempts": attempts,
                        "errorMessage": f"Job stalled and timed out after {MAX_ATTEMPTS} attempts.",
                        "failedAt": gc_firestore.SERVER_TIMESTAMP
                    })
                else:
                    job_ref.update({
                        "status": "queued",
                        "attempts": attempts,
                        "errorMessage": "Reset after processing stall."
                    })
        except Exception as e:
            logger.debug(f"Stall check note: {e}")

    def _process_next_job(self) -> bool:
        """
        Picks the oldest queued job, claims it atomically, and processes it.
        Returns True if a job was found and processed, False otherwise.
        """
        db = get_firestore()
        # Query queued jobs without composite index requirement
        docs = db.collection("fabricJobs") \
            .where("status", "==", "queued") \
            .limit(10) \
            .get()

        if not docs:
            return False

        def get_queue_time(d):
            q = d.to_dict().get("queuedAt")
            if hasattr(q, "timestamp"):
                return q.timestamp()
            if isinstance(q, (int, float)):
                return q
            return 0

        sorted_docs = sorted(docs, key=get_queue_time)
        doc = sorted_docs[0]
        job_id = doc.id
        job_ref = doc.reference

        # Atomic claim via transaction
        transaction = db.transaction()
        claimed = self._claim_job_transaction(transaction, job_ref)
        if not claimed:
            logger.info(f"Job {job_id} already claimed by another process.")
            return False

        logger.info(f"==> Successfully claimed job {job_id}. Processing...")
        self._execute_job(job_id, job_ref, claimed)
        self.jobs_processed += 1
        return True

    @staticmethod
    @gc_firestore.transactional
    def _claim_job_transaction(transaction, job_ref):
        snapshot = job_ref.get(transaction=transaction)
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        if data.get("status") != "queued":
            return None
        
        transaction.update(job_ref, {
            "status": "processing",
            "startedAt": gc_firestore.SERVER_TIMESTAMP
        })
        return data

    def _execute_job(self, job_id: str, job_ref, data: dict):
        try:
            business_id = data.get("businessId", "default")
            product_id = data.get("productId")
            template_id = data.get("garmentTemplateId", "kurta").lower().strip()
            source_url = data.get("sourcePhotoUrl")
            attempts = data.get("attempts", 0) + 1

            if not source_url:
                raise ValueError("Missing sourcePhotoUrl in job data.")

            template_dir = os.path.join(TEMPLATES_ROOT, template_id)
            if not os.path.exists(template_dir):
                # Fallback to kurta if invalid template requested
                logger.warning(f"Template {template_id} not found, falling back to kurta")
                template_dir = os.path.join(TEMPLATES_ROOT, "kurta")

            # 1. Fetch source fabric photo
            fabric_bytes = self._download_fabric_bytes(source_url)

            # 2. Clean and balance fabric
            cleaned_pil = clean_fabric_image(fabric_bytes)

            # 3. Drape onto template
            preview_pil, thumb_pil = drape_fabric_on_template(cleaned_pil, template_dir)

            # 4. Save to bytes
            preview_buf = io.BytesIO()
            preview_pil.save(preview_buf, format="JPEG", quality=92)
            preview_bytes = preview_buf.getvalue()

            thumb_buf = io.BytesIO()
            thumb_pil.save(thumb_buf, format="JPEG", quality=90)
            thumb_bytes = thumb_buf.getvalue()

            # 5. Upload to Cloud Storage
            preview_path = f"fabric_previews/{business_id}/{job_id}_preview.jpg"
            thumb_path = f"fabric_previews/{business_id}/{job_id}_thumb.jpg"

            try:
                preview_url = upload_image_to_storage(preview_bytes, preview_path)
                thumb_url = upload_image_to_storage(thumb_bytes, thumb_path)
            except Exception as se:
                logger.warning(f"Cloud Storage upload failed ({se}); fallback to Base64 data URI.")
                preview_b64 = base64.b64encode(preview_bytes).decode("ascii")
                thumb_b64 = base64.b64encode(thumb_bytes).decode("ascii")
                preview_url = f"data:image/jpeg;base64,{preview_b64}"
                thumb_url = f"data:image/jpeg;base64,{thumb_b64}"

            # 6. Mark complete in Firestore
            job_ref.update({
                "status": "complete",
                "completedAt": gc_firestore.SERVER_TIMESTAMP,
                "resultImageUrls": [preview_url],
                "resultThumbnailUrl": thumb_url,
                "attempts": attempts,
                "errorMessage": None
            })
            logger.info(f"✓ Job {job_id} COMPLETED successfully. Preview URL created.")

            # 7. Auto-attach to product if productId was specified
            if product_id:
                try:
                    db = get_firestore()
                    db.collection("products").document(product_id).update({
                        "fabricPreviewImage": preview_url,
                        "fabricThumbnailImage": thumb_url,
                        "fabricTemplateId": template_id,
                        "updatedAt": gc_firestore.SERVER_TIMESTAMP
                    })
                    logger.info(f"✓ Attached fabric preview to product {product_id}")
                except Exception as pe:
                    logger.warning(f"Could not update product {product_id}: {pe}")

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
            attempts = data.get("attempts", 0) + 1
            if attempts >= MAX_ATTEMPTS:
                job_ref.update({
                    "status": "failed",
                    "attempts": attempts,
                    "errorMessage": str(e),
                    "failedAt": gc_firestore.SERVER_TIMESTAMP
                })
            else:
                job_ref.update({
                    "status": "queued",
                    "attempts": attempts,
                    "errorMessage": f"Retryable error: {str(e)}"
                })

    def _download_fabric_bytes(self, source_url: str) -> bytes:
        if source_url.startswith("data:"):
            # Handle data URI
            header, encoded = source_url.split(",", 1)
            return base64.b64decode(encoded)
        elif source_url.startswith("http://") or source_url.startswith("https://"):
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                res = client.get(source_url)
                res.raise_for_status()
                return res.content
        elif os.path.exists(source_url):
            with open(source_url, "rb") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported sourcePhotoUrl format: {source_url[:30]}...")

worker = FabricQueueWorker()
