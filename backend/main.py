# ═══════════════════════════════════════════════════
# PixelMind — FastAPI Backend
# ═══════════════════════════════════════════════════

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import auth, user, ai, gallery, ads


# Create uploads directory on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    print("🚀 PixelMind API is running")
    yield
    print("👋 PixelMind API shutting down")


app = FastAPI(
    title="PixelMind API",
    description="AI-Powered Image Editing Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (serve uploaded/result images) ──
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/results", StaticFiles(directory="results"), name="results")

# ── Routers ──
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Tools"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["Gallery"])
app.include_router(ads.router, prefix="/api/ads", tags=["Ads"])


@app.get("/")
async def root():
    return {
        "name": "PixelMind API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
