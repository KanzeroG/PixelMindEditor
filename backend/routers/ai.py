# ═══════════════════════════════════════════
# AI Router — All 8 AI Tool Endpoints
# ═══════════════════════════════════════════

import time
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from PIL import Image

from middleware.auth import get_current_user_id
from models.schemas import AIResponse
from services.credit_service import deduct_credits, get_tool_cost
from services.ai_mock import process_image, save_result_image

router = APIRouter()


def get_user_from_store(user_id: str) -> dict:
    from routers.auth import users_db
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def handle_ai_request(
    tool_id: str,
    user_id: str,
    image_file: Optional[UploadFile] = None,
    prompt: str = "",
    strength: float = 0.75,
    seed: int = 42,
) -> AIResponse:
    """Common handler for all AI tool endpoints."""
    user = get_user_from_store(user_id)

    # Check credits
    success, remaining = deduct_credits(user, tool_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Need {get_tool_cost(tool_id)}, have {remaining}.",
        )

    start_time = time.time()

    try:
        # Load image if provided
        pil_image = None
        if image_file:
            contents = await image_file.read()
            pil_image = Image.open(BytesIO(contents))

        # Process
        result_image = await process_image(
            tool_id=tool_id,
            image=pil_image,
            prompt=prompt,
            strength=strength,
            seed=seed,
        )

        # Save result
        result_url = save_result_image(result_image)
        processing_time = time.time() - start_time

        return AIResponse(
            success=True,
            result_url=result_url,
            remaining_credits=user["credits"],
            processing_time=round(processing_time, 2),
        )

    except Exception as e:
        # Refund credits on error
        user["credits"] += get_tool_cost(tool_id)
        return AIResponse(
            success=False,
            remaining_credits=user["credits"],
            processing_time=time.time() - start_time,
            error=str(e),
        )


# ── Individual Endpoints ──

@router.post("/remove-bg", response_model=AIResponse)
async def remove_bg(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("remove-bg", user_id, image_file=image)


@router.post("/remove-object", response_model=AIResponse)
async def remove_object(
    image: UploadFile = File(...),
    prompt: str = Form(""),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("remove-object", user_id, image_file=image, prompt=prompt)


@router.post("/super-resolution", response_model=AIResponse)
async def super_resolution(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("super-resolution", user_id, image_file=image)


@router.post("/product-photo", response_model=AIResponse)
async def product_photo(
    image: UploadFile = File(...),
    prompt: str = Form(""),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("product-photo", user_id, image_file=image, prompt=prompt)


@router.post("/replace-bg", response_model=AIResponse)
async def replace_bg(
    image: UploadFile = File(...),
    prompt: str = Form(""),
    strength: float = Form(0.95),
    seed: int = Form(42),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request(
        "replace-bg",
        user_id,
        image_file=image,
        prompt=prompt,
        strength=strength,
        seed=seed,
    )


@router.post("/text-to-image", response_model=AIResponse)
async def text_to_image(
    prompt: str = Form(...),
    strength: float = Form(0.75),
    seed: int = Form(42),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("text-to-image", user_id, prompt=prompt, strength=strength, seed=seed)


@router.post("/uncrop", response_model=AIResponse)
async def uncrop(
    image: UploadFile = File(...),
    prompt: str = Form(""),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("uncrop", user_id, image_file=image, prompt=prompt)


@router.post("/remove-text", response_model=AIResponse)
async def remove_text(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_ai_request("remove-text", user_id, image_file=image)
