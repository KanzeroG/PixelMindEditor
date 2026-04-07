# PixelMind

AI-Powered Image Editing Platform — Software Engineering Course Project

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14 (App Router) + Tailwind CSS v4 | UI, SSR, routing |
| **Backend** | FastAPI (Python) | REST API, AI processing bridge |
| **Core Engine** | HuggingFace Diffusers (mock mode) | 8 AI image tools |
| **Database** | PostgreSQL + Prisma ORM | Users, credits, gallery |

## Quick Start

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows

# Always install with the backend venv interpreter (avoid global Python)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Verify PyTorch is using GPU (must print: True)
.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs
```

### Notes for GPU Inference
- This project is configured for CUDA-enabled PyTorch (GPU), not CPU-only inference.
- If `torch.cuda.is_available()` returns `False`, reinstall backend dependencies inside `backend/.venv` and ensure NVIDIA driver/CUDA runtime is available.

## Features
- 🎨 8 AI-powered image editing tools
- 💳 Compute credit system (10 free/day)
- 📺 Watch-ad-to-refill monetization
- 🖼 Personal gallery with sharing
- 🎯 Native ad integration (sponsored palettes, print CTA)
- 🌑 "Designer's Darkroom" pro-tool aesthetic

## Demo Account
- Email: `demo@pixelmind.ai`
- Password: `demo1234`
