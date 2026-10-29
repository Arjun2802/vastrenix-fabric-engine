import os
import io
import time
import base64
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.worker import worker, TEMPLATES_ROOT
from app.processing.cleanup import clean_fabric_image
from app.processing.texture_map import drape_fabric_on_template

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background queue polling worker
    worker.start()
    yield
    # Shutdown: Stop worker cleanly
    worker.stop()

app = FastAPI(
    title="Vastrenix Fabric Preview Engine",
    description="2D Mockup & drape compositing engine for textiles and ethnic garments.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for all origins (WebView + Web apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "vastrenix-fabric-engine",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    worker_alive = worker._thread is not None and worker._thread.is_alive()
    return {
        "status": "healthy" if worker_alive else "degraded",
        "worker_running": worker_alive,
        "jobs_processed": worker.jobs_processed,
        "last_poll_at": worker.last_poll_at.isoformat() if worker.last_poll_at else None,
        "timestamp": time.time()
    }

@app.get("/templates")
def list_templates():
    """
    Returns available garment templates and their configuration.
    """
    templates = []
    if os.path.exists(TEMPLATES_ROOT):
        for entry in os.listdir(TEMPLATES_ROOT):
            tdir = os.path.join(TEMPLATES_ROOT, entry)
            if os.path.isdir(tdir):
                templates.append({
                    "id": entry,
                    "name": entry.replace("_", " ").title(),
                    "mask_ready": os.path.exists(os.path.join(tdir, "silhouette_mask.png")),
                    "shading_ready": os.path.exists(os.path.join(tdir, "shading_overlay.png"))
                })
    return {"templates": templates}

@app.post("/render-sync")
async def render_sync(
    garment_template_id: str = Form("kurta"),
    scale: float = Form(0.7),
    file: UploadFile = File(...)
):
    """
    Direct synchronous preview rendering for immediate UI feedback.
    """
    template_dir = os.path.join(TEMPLATES_ROOT, garment_template_id.lower())
    if not os.path.exists(template_dir):
        raise HTTPException(status_code=400, detail=f"Garment template '{garment_template_id}' not found.")

    try:
        content = await file.read()
        cleaned_pil = clean_fabric_image(content)
        preview_pil, thumb_pil = drape_fabric_on_template(cleaned_pil, template_dir, scale=scale)

        p_buf = io.BytesIO()
        preview_pil.save(p_buf, format="JPEG", quality=90)
        p_b64 = base64.b64encode(p_buf.getvalue()).decode("ascii")

        t_buf = io.BytesIO()
        thumb_pil.save(t_buf, format="JPEG", quality=88)
        t_b64 = base64.b64encode(t_buf.getvalue()).decode("ascii")

        return {
            "status": "success",
            "garment_template_id": garment_template_id,
            "preview_data_url": f"data:image/jpeg;base64,{p_b64}",
            "thumbnail_data_url": f"data:image/jpeg;base64,{t_b64}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
