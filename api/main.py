import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from celery import Celery
from celery.result import AsyncResult
from api.schemas.sprite import GenerateSpriteRequest, TaskStatusResponse

app = FastAPI(title="Comfy Forge 2D API", description="Headless AI-driven 2D asset pipeline")

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
