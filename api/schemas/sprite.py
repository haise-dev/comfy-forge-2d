from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GenerateSpriteRequest(BaseModel):
    prompt: str
    negative_prompt: str = Field(default="blurry, low quality, deformed, white background")
    style_lora: str = Field(default="")
    seed: int = Field(default=-1)
    width: int = Field(default=512)
    height: int = Field(default=512)
    batch_size: int = Field(default=1)
    remove_background: bool = Field(default=True)

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)
