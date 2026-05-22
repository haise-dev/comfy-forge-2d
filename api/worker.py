import os
import json
import uuid
import urllib.request
import websocket
import random
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("comfy_tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(bind=True, name="generate_sprite_task")
def generate_sprite_task(self, request_dict: dict):
    ws = websocket.WebSocket()
    
    try:
        # Resolve path to json workflow
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "..", "comfy_workflows", "base_sprite.json")
        
        with open(json_path, "r") as f:
            workflow = json.load(f)

        # Inject dynamic values exactly like generate_sprite.py
        workflow["6"]["inputs"]["text"] = request_dict.get("prompt", "")
        workflow["7"]["inputs"]["text"] = request_dict.get("negative_prompt", "")
        
        final_seed = request_dict.get("seed", -1)
        if final_seed == -1:
            final_seed = random.randint(1, 9999999999)
        workflow["3"]["inputs"]["seed"] = final_seed

        # Dynamic LoRA Bypass Logic
        lora_path = os.path.join(script_dir, "..", "engine", "models", "loras", "pixel-art-v1.safetensors")
        lora_alt_path = os.path.join(script_dir, "..", "engine", "models", "loras", "pixel_art.safetensors")
        
        if not os.path.exists(lora_path) and not os.path.exists(lora_alt_path):
            # Bypass LoraLoader (node 10)
            workflow["3"]["inputs"]["model"] = ["4", 0]
            workflow["6"]["inputs"]["clip"] = ["4", 1]
            workflow["7"]["inputs"]["clip"] = ["4", 1]
            if "10" in workflow:
                del workflow["10"]
        else:
            # Inject actual filename
            if "10" in workflow:
                actual_name = "pixel_art.safetensors" if os.path.exists(lora_alt_path) else "pixel-art-v1.safetensors"
                workflow["10"]["inputs"]["lora_name"] = actual_name

        client_id = str(uuid.uuid4())
        
        def queue_prompt(prompt_workflow, client_id):
            p = {"prompt": prompt_workflow, "client_id": client_id}
            data = json.dumps(p).encode('utf-8')
            comfy_api_url = os.environ.get("COMFYUI_API_URL", "http://host.docker.internal:8188/prompt")
            req = urllib.request.Request(
                comfy_api_url, 
                data=data, 
                headers={'Content-Type': 'application/json'}
            )
            response = urllib.request.urlopen(req)
            return json.loads(response.read())

        comfy_ws_url = os.environ.get("COMFYUI_WS_URL", "ws://host.docker.internal:8188/ws")
        ws.connect(f"{comfy_ws_url}?clientId={client_id}")
        
        response = queue_prompt(workflow, client_id)
        prompt_id = response['prompt_id']
        generated_filename = "dummy_filename.png"

        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                
                msg_type = message.get('type')
                data = message.get('data', {})
                
                if msg_type == 'progress':
                    value = data.get('value', 0)
                    max_val = data.get('max', 1)
                    if max_val > 0:
                        current_progress = int((value / max_val) * 100)
                        self.update_state(state='PROCESSING', meta={'progress': current_progress})
                elif msg_type == 'executed':
                    output = data.get('output', {})
                    images = output.get('images', [])
                    if images:
                        generated_filename = images[0].get('filename', generated_filename)
                elif msg_type == 'executing':
                    node = data.get('node')
                    if node is None:
                        if data.get('prompt_id') == prompt_id:
                            return {"asset_urls": [f"/assets/{generated_filename}"]}

    except Exception as e:
        raise e
    finally:
        ws.close()

@celery_app.task(bind=True, name="download_style_lora_task")
def download_style_lora_task(self, style_id: str, url: str):
    self.update_state(state='PROCESSING', meta={'progress': 0})
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lora_dir = os.path.join(script_dir, "..", "engine", "models", "loras")
        os.makedirs(lora_dir, exist_ok=True)
        
        target_path = os.path.join(lora_dir, f"{style_id}.safetensors")
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(target_path, 'wb') as out_file:
            file_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                
                if file_size > 0:
                    progress = int((downloaded / file_size) * 100)
                    self.update_state(state='PROCESSING', meta={'progress': progress})
                    
        try:
            comfy_api_url = os.environ.get("COMFYUI_API_URL", "http://host.docker.internal:8188/prompt")
            refresh_url = comfy_api_url.replace("/prompt", "/object_info")
            urllib.request.urlopen(urllib.request.Request(refresh_url))
        except Exception as refresh_err:
            print(f"Warning: Failed to refresh ComfyUI cache: {refresh_err}")

        return {"status": "SUCCESS", "message": f"Downloaded {style_id} successfully.", "path": target_path}
    except Exception as e:
        self.update_state(state='FAILED', meta={'error': str(e)})
        raise e
