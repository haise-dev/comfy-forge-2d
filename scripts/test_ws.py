import json
import urllib.request
import urllib.parse
import uuid
import websocket
import os

# Ensure we can find the JSON file relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "..", "comfy_workflows", "base_sprite.json")

# Read the workflow JSON
with open(json_path, "r") as f:
    prompt = json.load(f)

# Generate a random client_id
client_id = str(uuid.uuid4())

def queue_prompt(prompt, client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

# Establish WebSocket connection
ws = websocket.WebSocket()
ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

print("Sending prompt execution request...")
response = queue_prompt(prompt, client_id)
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
                    print("Generation Complete")
                    break

ws.close()
