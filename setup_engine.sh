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

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
else
    echo "Virtual environment already exists. Skipping."
fi

echo "Installing PyTorch..."
uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121

echo "Installing ComfyUI dependencies..."
uv pip install -r requirements.txt

echo "Downloading Stable Diffusion 1.5 Base Model..."
mkdir -p models/checkpoints
if [ ! -s "models/checkpoints/v1-5-pruned-emaonly.safetensors" ]; then
    wget --no-check-certificate -O models/checkpoints/v1-5-pruned-emaonly.safetensors https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors
else
    echo "Model already exists, skipping download."
fi

echo ""
echo "### DOWNLOADING LORA ASSETS ###"
mkdir -p models/loras

FILE1="models/loras/pixel_art.safetensors"
if [ ! -f "$FILE1" ] || [ $(stat -c%s "$FILE1" 2>/dev/null || stat -f%z "$FILE1" 2>/dev/null || echo 0) -lt 1000000 ]; then
    echo "Downloading LoRA 1/4: Pixel Art V1..."
    curl -L -# -A "Mozilla/5.0" -o models/loras/pixel_art.safetensors "https://huggingface.co/patchai/pixel-art-style/media/main/pixel-art-style.safetensors"
else
    echo "Pixel Art V1 LoRA already exists and is valid. Skipping."
fi

FILE2="models/loras/isometric_asset.safetensors"
if [ ! -f "$FILE2" ] || [ $(stat -c%s "$FILE2" 2>/dev/null || stat -f%z "$FILE2" 2>/dev/null || echo 0) -lt 1000000 ]; then
    echo "Downloading LoRA 2/4: Isometric Game Asset..."
    curl -L -# -A "Mozilla/5.0" -o models/loras/isometric_asset.safetensors "https://huggingface.co/Dunkindunuts/IsometricLORA/media/main/IsometricV1.safetensors"
else
    echo "Isometric Game Asset LoRA already exists and is valid. Skipping."
fi

FILE3="models/loras/ghibli_style.safetensors"
if [ ! -f "$FILE3" ] || [ $(stat -c%s "$FILE3" 2>/dev/null || stat -f%z "$FILE3" 2>/dev/null || echo 0) -lt 1000000 ]; then
    echo "Downloading LoRA 3/4: Ghibli Studio..."
    curl -L -# -A "Mozilla/5.0" -o models/loras/ghibli_style.safetensors "https://huggingface.co/IAmTheGamer/Ghibli-Style-LoRA/media/main/ghibli_style_v1.safetensors"
else
    echo "Ghibli Studio LoRA already exists and is valid. Skipping."
fi

FILE4="models/loras/dark_fantasy.safetensors"
if [ ! -f "$FILE4" ] || [ $(stat -c%s "$FILE4" 2>/dev/null || stat -f%z "$FILE4" 2>/dev/null || echo 0) -lt 1000000 ]; then
    echo "Downloading LoRA 4/4: Dark Fantasy..."
    curl -L -# -A "Mozilla/5.0" -o models/loras/dark_fantasy.safetensors "https://huggingface.co/wooyvern/sd-1.5-dark-fantasy-1.1/resolve/main/Dark%20Fantasy%20v1.1.safetensors"
else
    echo "Dark Fantasy LoRA already exists and is valid. Skipping."
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
echo "3. Start the Next.js UI Portal:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
