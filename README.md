# Comfy Forge 2D ⚔️

A headless, asynchronous API pipeline for generating 2D game assets using ComfyUI, FastAPI, Celery, and Redis.

## System Architecture (Hybrid Approach)

To maximize GPU performance and avoid bloated 20GB+ Docker images, this project utilizes a **Hybrid Architecture** approach:
- **Core Engine (ComfyUI + PyTorch):** Runs directly on the bare-metal Ubuntu host machine for direct hardware and VRAM access.
- **API Services (FastAPI + Celery Worker + Redis):** Run inside an isolated Docker Compose network, communicating back to the host engine securely.

## Prerequisites

- Linux/Ubuntu OS
- NVIDIA GPU (RTX 30 series or higher / CUDA 12.1 recommended)
- Python 3.12+
- `uv` package manager
- Docker and Docker Compose

## Quick Start

**Step 1:** Clone the repository
```bash
git clone https://github.com/your-username/comfy-forge-2d.git
cd comfy-forge-2d
```

**Step 2:** Run the automated setup script to install ComfyUI and download the SD 1.5 base model
```bash
./setup_engine.sh
```

**Step 3:** Start the bare-metal engine
```bash
source engine/.venv/bin/activate
python engine/main.py --listen
```

**Step 4:** Start the API microservices
In a new terminal window, run:
```bash
docker compose up -d
```

**Step 5:** Start the Frontend UI Portal
In a new terminal window, run:
```bash
cd frontend
npm run dev
```

## API Contract

The application exposes the following primary REST endpoints:

### Generate Sprite
`POST /api/v1/sprites/generate`
- **Payload:** Accepts a JSON object containing `prompt`, `negative_prompt`, and `seed`.
- **Response:** Asynchronously returns a tracking `task_id`.

### Task Status
`GET /api/v1/tasks/{task_id}`
- **Response:** Returns the current state of the generation (`PENDING`, `PROCESSING`, `SUCCESS`, or `FAILED`). Upon success, the payload will contain the hosted image links within the `asset_urls` array.
