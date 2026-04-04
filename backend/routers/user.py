# ═══════════════════════════════════════════
# User Router — Profile & Credits
# ═══════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth import get_current_user_id
from models.schemas import UserResponse, CreditRefillResponse
from services.credit_service import refill_credits, check_and_reset_daily_credits

router = APIRouter()


def get_user_from_store(user_id: str) -> dict:
    """Get user from in-memory store (imported from auth router)."""
    from routers.auth import users_db

    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/me", response_model=UserResponse)
async def get_profile(user_id: str = Depends(get_current_user_id)):
    user = get_user_from_store(user_id)
    check_and_reset_daily_credits(user)

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        credits=user["credits"],
        created_at=user["created_at"],
    )


@router.post("/credits/refill", response_model=CreditRefillResponse)
async def refill_user_credits(user_id: str = Depends(get_current_user_id)):
    user = get_user_from_store(user_id)
    new_credits = refill_credits(user)

    return CreditRefillResponse(
        credits=new_credits,
        message=f"Refilled! You now have {new_credits} credits.",
    )
