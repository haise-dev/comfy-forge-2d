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

        client_id = str(uuid.uuid4())
        
        def queue_prompt(prompt_workflow, client_id):
            p = {"prompt": prompt_workflow, "client_id": client_id}
            data = json.dumps(p).encode('utf-8')
            comfy_api_url = os.environ.get("COMFYUI_API_URL", "http://127.0.0.1:8188/prompt")
            req = urllib.request.Request(
                comfy_api_url, 
                data=data, 
                headers={'Content-Type': 'application/json'}
            )
            response = urllib.request.urlopen(req)
            return json.loads(response.read())

        comfy_ws_url = os.environ.get("COMFYUI_WS_URL", "ws://127.0.0.1:8188/ws")
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
