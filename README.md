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
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs
```

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
