import os
import json
import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, storage

logger = logging.getLogger("fabric-engine.firebase")

_app = None
_db = None
_bucket = None

def get_firebase_app():
    global _app, _db, _bucket
    if _app is not None:
        return _app

    service_account_raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    cred = None
    if service_account_raw:
        try:
            # Parse JSON string from env var
            data = json.loads(service_account_raw)
            cred = credentials.Certificate(data)
            logger.info("Loaded Firebase credentials from FIREBASE_SERVICE_ACCOUNT_JSON env var")
        except Exception as e:
            logger.error(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            raise

    elif service_account_path and os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        logger.info(f"Loaded Firebase credentials from file: {service_account_path}")
    else:
        # Check standard fallback path
        local_fallback = "/Users/codekajugad/Desktop/Vastranix/firebase-service-account.json"
        if os.path.exists(local_fallback):
            cred = credentials.Certificate(local_fallback)
            logger.info(f"Loaded Firebase credentials from local fallback: {local_fallback}")
        else:
            raise RuntimeError("No Firebase credentials provided. Set FIREBASE_SERVICE_ACCOUNT_JSON.")

    # Storage bucket name defaults to vastranix.appspot.com or vastranix.firebasestorage.app
    bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET", "vastranix.firebasestorage.app")
    _app = firebase_admin.initialize_app(cred, {
        "storageBucket": bucket_name
    })
    _db = firestore.client()
    try:
        _bucket = storage.bucket()
    except Exception as e:
        logger.warning(f"Storage bucket init warning: {e}")

    return _app

def get_firestore():
    get_firebase_app()
    return _db

def get_storage_bucket():
    get_firebase_app()
    return _bucket

def upload_image_to_storage(image_bytes: bytes, destination_path: str, content_type: str = "image/jpeg") -> str:
    """
    Uploads bytes to Firebase Cloud Storage and returns a publicly accessible URL or download token URL.
    """
    bucket = get_storage_bucket()
    if not bucket:
        raise RuntimeError("Cloud Storage bucket is not available")

    blob = bucket.blob(destination_path)
    # Using fixed metadata token for public download URL
    import uuid
    download_token = str(uuid.uuid4())
    blob.metadata = {"firebaseStorageDownloadTokens": download_token}
    
    blob.upload_from_string(image_bytes, content_type=content_type)
    
    # Standard Firebase Storage direct download URL format
    encoded_path = destination_path.replace("/", "%2F")
    bucket_name = bucket.name
    public_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{encoded_path}?alt=media&token={download_token}"
    return public_url
