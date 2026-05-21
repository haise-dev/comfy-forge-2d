import argparse
import json
import urllib.request
import urllib.parse
import uuid
import websocket
import os
import random

'''
python scripts/generate_sprite.py \
  --prompt "isometric health potion, glowing red liquid, glass flask, pixel art, 2d game sprite, transparent background" \
  --negative "blurry, low quality, deformed, realistic, 3d render" \
  --seed 8888
'''

def main():
    parser = argparse.ArgumentParser(description="Generate 2D sprite via ComfyUI API")
    parser.add_argument("--prompt", type=str, required=True, help="Positive prompt for the sprite")
    parser.add_argument("--negative", type=str, default="blurry, low quality, deformed", help="Negative prompt")
    parser.add_argument("--seed", type=int, default=random.randint(1, 9999999999), help="Random seed")
    
    args = parser.parse_args()

    # Ensure we can find the JSON file relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "..", "comfy_workflows", "base_sprite.json")

    # Read the workflow JSON
    with open(json_path, "r") as f:
        workflow = json.load(f)

    # INJECT dynamic values
    workflow["6"]["inputs"]["text"] = args.prompt
    workflow["7"]["inputs"]["text"] = args.negative
    workflow["3"]["inputs"]["seed"] = args.seed

    # Generate a random client_id
    client_id = str(uuid.uuid4())

    def queue_prompt(prompt_workflow, client_id):
        p = {"prompt": prompt_workflow, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
        response = urllib.request.urlopen(req)
        return json.loads(response.read())

    # Establish WebSocket connection
    ws = websocket.WebSocket()
    ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

    print(f"Generating sprite with seed {args.seed}...")
    print("Sending prompt execution request...")
    response = queue_prompt(workflow, client_id)
    prompt_id = response['prompt_id']

    print(f"Prompt queued with ID: {prompt_id}")
    print("Listening to WebSocket for progress events...")

    # Listen to the WebSocket stream
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            
            msg_type = message.get('type')
            data = message.get('data', {})
            
            if msg_type == 'progress':
                print(f"Progress: {data.get('value')}/{data.get('max')}")
            elif msg_type == 'execution_start':
                print(f"Execution started for prompt: {data.get('prompt_id')}")
            elif msg_type == 'executing':
                node = data.get('node')
                if node is not None:
                    print(f"Executing node: {node}")
                else:
                    # Execution finishes when node is None for the corresponding prompt
                    if data.get('prompt_id') == prompt_id:
                        print("Asset Generated Successfully.")
                        break

    ws.close()

if __name__ == "__main__":
    main()
