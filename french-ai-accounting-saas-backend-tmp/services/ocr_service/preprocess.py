"""
Lightweight image preprocessing for OCR robustness.

Goals:
- Improve OCR on noisy scans (grayscale, denoise, contrast, threshold)
- Preserve important tokens like French decimal commas (e.g. "597,60")

This module is intentionally dependency-light (Pillow only).
"""

from __future__ import annotations

import io
from typing import Literal, Tuple

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


PreprocessMode = Literal["standard", "aggressive"]


def preprocess_pil_image(img: Image.Image, *, mode: PreprocessMode = "standard") -> Image.Image:
    """
    Return a new PIL image enhanced for OCR.

    - standard: good default for receipts/invoices
    - aggressive: stronger thresholding for very low-contrast scans
    """
    base = img.convert("L")  # grayscale

    # Denoise while keeping edges.
    base = base.filter(ImageFilter.MedianFilter(size=3))

    # Improve contrast.
    base = ImageOps.autocontrast(base)
    base = ImageEnhance.Contrast(base).enhance(1.6 if mode == "standard" else 2.0)
    base = ImageEnhance.Sharpness(base).enhance(1.2 if mode == "standard" else 1.4)

    # Threshold (binarize).
    # Keep threshold conservative in standard mode to avoid dropping commas/decimal separators.
    thresh = 155 if mode == "standard" else 175
    bw = base.point(lambda p: 255 if p > thresh else 0, mode="1")

    # Tesseract generally works best with 8-bit or RGB; convert back to L.
    return bw.convert("L")


def preprocess_image_bytes_to_png(
    image_bytes: bytes,
    *,
    mode: PreprocessMode = "standard",
) -> Tuple[bytes, str]:
    """
    Preprocess an image and return PNG bytes + a short description of the mode used.
    """
    img = Image.open(io.BytesIO(image_bytes))
    out_img = preprocess_pil_image(img, mode=mode)
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    return buf.getvalue(), mode

