import asyncio
import os
import threading
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image
from rembg import new_session, remove


BASE_MODEL = os.getenv("REPLACEBG_BASE_MODEL", "runwayml/stable-diffusion-inpainting")
LORA_MODEL_PATH = Path(
    os.getenv(
        "REPLACEBG_LORA_PATH",
        str(Path(__file__).resolve().parent.parent / "models" / "replacebg_lora.pt"),
    )
)
DEFAULT_PROMPT = os.getenv(
    "REPLACEBG_DEFAULT_PROMPT",
    "modern office interior, realistic photo, soft natural light",
)
DEFAULT_NEGATIVE_PROMPT = os.getenv(
    "REPLACEBG_NEGATIVE_PROMPT",
    "blurry, low quality, artifacts, extra limbs, text, watermark",
)
DEFAULT_STEPS = int(os.getenv("REPLACEBG_STEPS", "30"))
DEFAULT_GUIDANCE = float(os.getenv("REPLACEBG_GUIDANCE", "7.5"))
MAX_SIDE = int(os.getenv("REPLACEBG_MAX_SIDE", "1024"))


_PIPELINE: Optional[StableDiffusionInpaintPipeline] = None
_MASK_SESSION = None
_INIT_LOCK = threading.Lock()
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _resize_for_inference(image: Image.Image) -> Tuple[Image.Image, Tuple[int, int]]:
    width, height = image.size
    scale = min(1.0, MAX_SIDE / max(width, height))
    new_w = max(8, int(width * scale))
    new_h = max(8, int(height * scale))

    # Diffusers inpainting expects dimensions aligned to multiples of 8.
    new_w = max(8, (new_w // 8) * 8)
    new_h = max(8, (new_h // 8) * 8)

    if (new_w, new_h) == (width, height):
        return image, (width, height)

    return image.resize((new_w, new_h), Image.LANCZOS), (width, height)


def _load_lora_weights(pipe: StableDiffusionInpaintPipeline) -> None:
    if not LORA_MODEL_PATH.exists():
        raise FileNotFoundError(f"LoRA file not found: {LORA_MODEL_PATH}")

    model_dir = str(LORA_MODEL_PATH.parent)
    weight_name = LORA_MODEL_PATH.name
    load_from_path_error: Optional[Exception] = None

    try:
        pipe.load_lora_weights(model_dir, weight_name=weight_name)
        return
    except Exception as err:
        load_from_path_error = err
        pass

    try:
        state = torch.load(LORA_MODEL_PATH, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state and isinstance(state["state_dict"], dict):
            state = state["state_dict"]
        if not isinstance(state, dict):
            raise TypeError(f"Unsupported .pt content type: {type(state)}")
        pipe.load_lora_weights(state)
    except Exception as load_from_dict_error:
        raise RuntimeError(
            f"Failed to load LoRA weights from {LORA_MODEL_PATH}. "
            f"Path load error: {load_from_path_error}; Dict load error: {load_from_dict_error}"
        ) from load_from_dict_error


def _get_pipeline() -> StableDiffusionInpaintPipeline:
    global _PIPELINE

    if _PIPELINE is not None:
        return _PIPELINE

    with _INIT_LOCK:
        if _PIPELINE is not None:
            return _PIPELINE

        dtype = torch.float16 if _DEVICE == "cuda" else torch.float32
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            BASE_MODEL,
            torch_dtype=dtype,
            safety_checker=None,
        )
        if _DEVICE == "cuda":
            pipe = pipe.to("cuda")

        pipe.enable_attention_slicing()
        _load_lora_weights(pipe)
        _PIPELINE = pipe

    return _PIPELINE


def _get_mask_session():
    global _MASK_SESSION

    if _MASK_SESSION is not None:
        return _MASK_SESSION

    with _INIT_LOCK:
        if _MASK_SESSION is None:
            _MASK_SESSION = new_session("u2net_human_seg")

    return _MASK_SESSION


def _build_inpaint_mask(image: Image.Image) -> Image.Image:
    fg_rgba = remove(image.convert("RGB"), session=_get_mask_session())
    alpha = np.array(fg_rgba)[:, :, 3]
    return Image.fromarray(255 - alpha).convert("L")


def _run_replace_background(
    image: Image.Image,
    prompt: str = "",
    strength: float = 0.95,
    seed: int = 42,
) -> Image.Image:
    if image is None:
        raise ValueError("Image is required for replace-bg")

    image = image.convert("RGB")
    image_for_model, original_size = _resize_for_inference(image)
    mask = _build_inpaint_mask(image_for_model)

    pipeline = _get_pipeline()
    clean_prompt = prompt.strip() or DEFAULT_PROMPT
    steps = int(_clamp(DEFAULT_STEPS, 10, 80))
    guidance = float(_clamp(DEFAULT_GUIDANCE, 1.0, 20.0))
    strength = float(_clamp(strength, 0.5, 1.0))

    generator = torch.Generator(device=_DEVICE).manual_seed(int(seed))

    with torch.inference_mode():
        out = pipeline(
            prompt=clean_prompt,
            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            image=image_for_model,
            mask_image=mask,
            num_inference_steps=steps,
            guidance_scale=guidance,
            strength=strength,
            generator=generator,
        ).images[0]

    if out.size != original_size:
        out = out.resize(original_size, Image.LANCZOS)

    return out.convert("RGB")


async def replace_background(
    image: Image.Image,
    prompt: str = "",
    strength: float = 0.95,
    seed: int = 42,
) -> Image.Image:
    return await asyncio.to_thread(_run_replace_background, image, prompt, strength, seed)
