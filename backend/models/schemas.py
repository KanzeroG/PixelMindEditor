# ═══════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Auth ──
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


# ── User ──
class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    credits: int
    created_at: Optional[datetime] = None


class CreditRefillResponse(BaseModel):
    credits: int
    message: str


# ── AI ──
class AIResponse(BaseModel):
    success: bool
    result_url: Optional[str] = None
    remaining_credits: int
    processing_time: float
    error: Optional[str] = None


# ── Gallery ──
class ProjectCreate(BaseModel):
    title: str = "Untitled"
    image_url: Optional[str] = None
    result_url: Optional[str] = None
    tool_used: Optional[str] = None
    prompt: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    image_url: Optional[str]
    result_url: Optional[str]
    tool_used: Optional[str]
    prompt: Optional[str]
    is_public: bool
    created_at: datetime


# ── Ads ──
class AdImpressionCreate(BaseModel):
    ad_type: str  # "sponsored_palette", "print_cta", "video_refill"
    ad_brand: Optional[str] = None
    clicked: bool = False


class TransactionType(str, Enum):
    DEDUCTION = "DEDUCTION"
    DAILY_RESET = "DAILY_RESET"
    AD_REFILL = "AD_REFILL"
    ADMIN_GRANT = "ADMIN_GRANT"
