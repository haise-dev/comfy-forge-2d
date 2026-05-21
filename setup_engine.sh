#!/bin/bash
set -e

echo "🚀 Setting up Comfy Forge 2D Engine..."

if [ ! -d "engine" ]; then
    echo "Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git engine
else
    echo "engine directory already exists, skipping clone."
fi

cd engine/

echo "Creating virtual environment..."
uv venv

echo "Installing PyTorch..."
uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121

echo "Installing ComfyUI dependencies..."
uv pip install -r requirements.txt

echo "Downloading Stable Diffusion 1.5 Base Model..."
mkdir -p models/checkpoints
if [ ! -f "models/checkpoints/v1-5-pruned-emaonly.safetensors" ]; then
    wget -O models/checkpoints/v1-5-pruned-emaonly.safetensors https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors
else
    echo "Model already exists, skipping download."
fi

echo ""
echo "✅ Setup Complete!"
echo "To start the application, run the following commands in separate terminals:"
echo ""
echo "1. Start the ComfyUI Engine:"
echo "   source engine/.venv/bin/activate"
echo "   python engine/main.py --listen"
echo ""
echo "2. Start the FastAPI microservice:"
echo "   docker compose up -d"
echo ""
