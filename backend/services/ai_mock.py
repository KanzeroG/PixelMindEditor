# ═══════════════════════════════════════════
# AI Mock Service — Simulated Responses
# ═══════════════════════════════════════════

import asyncio
import os
import uuid
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter


async def mock_remove_bg(image: Image.Image) -> Image.Image:
    """Simulate background removal by making edges transparent."""
    await asyncio.sleep(2)
    result = image.convert("RGBA")
    # Simple mock: just return the image as-is (real impl would use rembg)
    return result


async def mock_remove_object(image: Image.Image, mask: Image.Image = None) -> Image.Image:
    """Simulate object removal with blur on masked area."""
    await asyncio.sleep(2.5)
    result = image.copy()
    # Mock: apply slight blur to simulate inpainting
    result = result.filter(ImageFilter.GaussianBlur(radius=2))
    # Blend original with blurred
    return Image.blend(image, result, 0.3)


async def mock_super_resolution(image: Image.Image) -> Image.Image:
    """Simulate 4x upscale."""
    await asyncio.sleep(3.5)
    w, h = image.size
    return image.resize((w * 2, h * 2), Image.LANCZOS)


async def mock_product_photo(image: Image.Image, prompt: str = "") -> Image.Image:
    """Simulate product photo enhancement."""
    await asyncio.sleep(2)
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    result = enhancer.enhance(1.3)
    enhancer = ImageEnhance.Brightness(result)
    result = enhancer.enhance(1.1)
    return result


async def mock_replace_bg(image: Image.Image, prompt: str = "") -> Image.Image:
    """Simulate background replacement."""
    await asyncio.sleep(2.5)
    result = image.copy()
    # Mock: add a colored overlay to simulate new background
    overlay = Image.new("RGBA", image.size, (139, 92, 246, 40))
    if result.mode != "RGBA":
        result = result.convert("RGBA")
    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")


async def mock_text_to_image(prompt: str, seed: int = 42) -> Image.Image:
    """Generate a placeholder image for text-to-image."""
    await asyncio.sleep(3)
    img = Image.new("RGB", (512, 512), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    # Draw gradient background
    for y in range(512):
        r = int(139 * (y / 512))
        g = int(92 * (1 - y / 512))
        b = int(246 * (y / 512))
        draw.line([(0, y), (512, y)], fill=(r, g, b))

    # Add text overlay
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except (OSError, IOError):
        font = ImageFont.load_default()

    draw.text((256, 230), "AI Generated", fill=(255, 255, 255, 180), anchor="mm", font=font)
    if prompt:
        short_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
        draw.text((256, 260), f'"{short_prompt}"', fill=(255, 255, 255, 120), anchor="mm", font=font)

    # Add seed marker
    draw.text((10, 490), f"seed: {seed}", fill=(255, 255, 255, 80), font=font)

    return img


async def mock_uncrop(image: Image.Image, prompt: str = "") -> Image.Image:
    """Simulate outpainting by extending canvas."""
    await asyncio.sleep(3.5)
    w, h = image.size
    new_w, new_h = int(w * 1.4), int(h * 1.4)
    result = Image.new("RGB", (new_w, new_h), (26, 26, 26))

    # Paste original in center
    offset_x = (new_w - w) // 2
    offset_y = (new_h - h) // 2
    result.paste(image, (offset_x, offset_y))

    return result


async def mock_remove_text(image: Image.Image) -> Image.Image:
    """Simulate text removal with slight blur."""
    await asyncio.sleep(2)
    return image.filter(ImageFilter.MedianFilter(size=3))


# ── Router Dispatch ──
MOCK_HANDLERS = {
    "remove-bg": mock_remove_bg,
    "remove-object": mock_remove_object,
    "super-resolution": mock_super_resolution,
    "product-photo": mock_product_photo,
    "replace-bg": mock_replace_bg,
    "text-to-image": mock_text_to_image,
    "uncrop": mock_uncrop,
    "remove-text": mock_remove_text,
}


async def process_image(
    tool_id: str,
    image: Image.Image = None,
    prompt: str = "",
    strength: float = 0.75,
    seed: int = 42,
) -> Image.Image:
    """Route to the correct mock handler."""
    handler = MOCK_HANDLERS.get(tool_id)
    if not handler:
        raise ValueError(f"Unknown tool: {tool_id}")

    if tool_id == "text-to-image":
        return await handler(prompt, seed)
    elif tool_id in ("product-photo", "replace-bg", "uncrop"):
        return await handler(image, prompt)
    else:
        return await handler(image)


def save_result_image(image: Image.Image) -> str:
    """Save result image and return the URL path."""
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join("results", filename)
    os.makedirs("results", exist_ok=True)

    if image.mode == "RGBA":
        image.save(filepath, "PNG")
    else:
        image.save(filepath, "PNG")

    return f"/results/{filename}"
