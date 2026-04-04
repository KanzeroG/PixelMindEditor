# ═══════════════════════════════════════════
# Auth Router — Register & Login
# ═══════════════════════════════════════════

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from models.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from middleware.auth import hash_password, verify_password, create_access_token
from services.credit_service import INITIAL_CREDITS

router = APIRouter()

# ── In-Memory User Store (replace with DB in production) ──
users_db: dict[str, dict] = {}

# Pre-seed a demo user
DEMO_USER_ID = str(uuid.uuid4())
users_db[DEMO_USER_ID] = {
    "id": DEMO_USER_ID,
    "email": "demo@pixelmind.ai",
    "name": "Demo User",
    "password_hash": hash_password("demo1234"),
    "credits": INITIAL_CREDITS,
    "last_credit_reset": datetime.now(timezone.utc),
    "created_at": datetime.now(timezone.utc),
}


def find_user_by_email(email: str):
    for user in users_db.values():
        if user["email"] == email:
            return user
    return None


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    # Check if email exists
    if find_user_by_email(req.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": req.email,
        "name": req.name,
        "password_hash": hash_password(req.password),
        "credits": INITIAL_CREDITS,
        "last_credit_reset": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }
    users_db[user_id] = user

    token = create_access_token({"sub": user_id, "email": req.email})

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=req.email,
            name=req.name,
            credits=INITIAL_CREDITS,
            created_at=user["created_at"],
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = find_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user["id"], "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            credits=user["credits"],
            created_at=user["created_at"],
        ),
    )
