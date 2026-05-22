import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from celery import Celery
from celery.result import AsyncResult
from api.schemas.sprite import GenerateSpriteRequest, TaskStatusResponse

app = FastAPI(title="Comfy Forge 2D API", description="Headless AI-driven 2D asset pipeline")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine", "output")
app.mount("/assets", StaticFiles(directory=output_dir), name="assets")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("comfy_tasks", broker=REDIS_URL, backend=REDIS_URL)

@app.post("/api/v1/sprites/generate", response_model=TaskStatusResponse)
async def generate_sprite(request: GenerateSpriteRequest):
    task = celery_app.send_task("generate_sprite_task", args=[request.model_dump()])
    return TaskStatusResponse(
        task_id=task.id,
        status="PENDING",
        progress=0,
        result=None,
        error=None
    )

@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    
    # Map Celery states to our API states
    status_map = {
        "PENDING": "PENDING",
        "STARTED": "PROCESSING",
        "PROCESSING": "PROCESSING",
        "SUCCESS": "SUCCESS",
        "FAILURE": "FAILED",
        "RETRY": "PROCESSING",
        "REVOKED": "FAILED"
    }
    
    status = status_map.get(res.state, res.state)
    
    progress = 0
    if res.state == 'PROCESSING' or res.state == 'STARTED':
        if isinstance(res.info, dict):
            progress = res.info.get('progress', 0)
    elif res.state == 'SUCCESS':
        progress = 100
        
    result = None
    error = None
    
    if res.state == 'SUCCESS':
        result = res.result
    elif res.state == 'FAILURE':
        error = str(res.result)

    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        progress=progress,
        result=result,
        error=error
    )

class DownloadStyleRequest(BaseModel):
    style_id: str

AVAILABLE_STYLES = {
    "pixel_art": {
        "name": "Retro Pixel Art",
        "url": "https://civitai.com/api/download/models/43820",
        "filename": "pixel-art-v1.safetensors"
    }
}

@app.post("/api/v1/styles/download")
async def download_style(request: DownloadStyleRequest):
    if request.style_id not in AVAILABLE_STYLES:
        raise HTTPException(status_code=404, detail="Style not found")
    
    style_info = AVAILABLE_STYLES[request.style_id]
    task = celery_app.send_task("download_style_lora_task", args=[request.style_id, style_info["url"]])
    
    return {"task_id": task.id, "status": "PENDING"}

@app.get("/api/v1/styles/progress/{task_id}")
async def get_style_progress(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    
    status_map = {
        "PENDING": "PENDING",
        "STARTED": "PROCESSING",
        "PROCESSING": "PROCESSING",
        "SUCCESS": "SUCCESS",
        "FAILURE": "FAILED",
        "RETRY": "PROCESSING",
        "REVOKED": "FAILED"
    }
    
    status = status_map.get(res.state, res.state)
    
    progress = 0
    if status == 'PROCESSING':
        if isinstance(res.info, dict):
            progress = res.info.get('progress', 0)
    elif status == 'SUCCESS':
        progress = 100
        
    response_data = {
        "task_id": task_id,
        "status": status,
        "progress": progress
    }
    
    if status == 'SUCCESS':
        response_data["result"] = res.result
    elif status == 'FAILED':
        response_data["error"] = str(res.result)
        
    return response_data
