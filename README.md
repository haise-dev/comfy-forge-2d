# 🛠️ ComfyForge 2D

**A Headless AI-Driven 2D Asset Pipeline for Indie Game Developers.**

ComfyForge 2D is an open-source, 100% local microservice that wraps the power of [ComfyUI](https://github.com/comfyanonymous/ComfyUI) and Stable Diffusion into a seamless RESTful API. It is designed to automate the process of generating game-ready 2D sprites, props, and assets—from text prompts to transparent PNGs—without requiring developers to interact with complex node graphs.

## ✨ Core Features (Planned)

*   **Headless Inference API:** Communicate with ComfyUI entirely via a clean FastAPI REST interface.
*   **Auto Background Removal:** Built-in nodes to automatically strip backgrounds (alpha channel) and return transparent PNGs ready for game engines (Unity, Godot).
*   **Style Consistency Enforcement:** Easily pass LoRA parameters via API to lock in your specific game's art style (e.g., pixel art, dark fantasy).
*   **Plug-and-Play Deployment:** Fully containerized using Docker and Docker Compose for instant local deployment.

## 🏗️ Tech Stack

*   **AI Engine:** ComfyUI, Stable Diffusion (1.5 / SDXL), Rembg
*   **Backend Wrapper:** Python, FastAPI
*   **Task Queue:** Redis & Celery (Planned)
*   **Infrastructure:** Docker, Docker Compose
*   **Hardware Target:** Optimized for Single GPU (e.g., RTX 3080 16GB) on Linux/Ubuntu.
