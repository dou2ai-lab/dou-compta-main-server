"""
PaddleOCR Provider
CPU-friendly OCR using PaddleOCR with optional PDF → image pipeline.

Dependencies (install in your environment):
    pip install "paddlepaddle>=2.6.2" "paddleocr>=2.7.0.3" pdf2image opencv-python pillow
    (Use 2.6.2 or 3.x if 2.6.1 is not available for your platform.)
PDF support: either (1) Poppler (pdf2image) — install poppler and set POPPLER_PATH
on Windows, or (2) PyMuPDF fallback — pip install pymupdf (no external binaries).
"""
from __future__ import annotations

import io
import os
from typing import Dict, List, Tuple, Any

import structlog
from PIL import Image

from .provider import OCRProvider

logger = structlog.get_logger()


class PaddleOCRProvider(OCRProvider):
    """PaddleOCR provider implementation with basic PDF support."""

    def __init__(self) -> None:
        # Import lazily so the rest of the service can run even if PaddleOCR
        # (and its heavy dependencies) are not installed.
        try:
            from paddleocr import PaddleOCR  # type: ignore

            # Single shared OCR instance (CPU, French + English).
            # PaddleOCR 3.x removed show_log; use_angle_cls and lang are supported.
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="fr",  # good default for France; English still works reasonably
            )
            logger.info("paddleocr_initialized", engine="PaddleOCR")
        except Exception as e:  # pragma: no cover - import/runtime issues
            logger.error(
                "paddleocr_init_failed",
                error=str(e),
                message="Install paddlepaddle, paddleocr, pdf2image and opencv-python for PaddleOCR support.",
            )
            self._ocr = None

    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """
        Extract text using PaddleOCR.

        Handles:
        - Image types supported by PIL (png/jpg/webp, etc.)
        - PDFs (first few pages) via pdf2image, if available
        """
        if self._ocr is None:
            logger.warning(
                "paddleocr_not_available",
                message="Falling back to empty OCR result; install PaddleOCR and dependencies.",
            )
            return {
                "text": "",
                "raw_response": {"error": "PaddleOCR not available"},
                "confidence_scores": {},
                "extraction_method": "paddleocr_unavailable",
            }

        images: List[Image.Image] = []
        try:
            if mime_type == "application/pdf":
                images = self._pdf_to_images(file_content)
            else:
                images = [Image.open(io.BytesIO(file_content))]
        except Exception as e:  # pragma: no cover - defensive
            logger.error("paddleocr_image_load_failed", error=str(e), mime_type=mime_type, exc_info=True)
            return {
                "text": "",
                "raw_response": {"error": f"Failed to load image/PDF: {e}"},
                "confidence_scores": {},
                "extraction_method": "paddleocr_image_load_failed",
            }

        all_lines: List[str] = []
        all_scores: List[float] = []
        raw_results: List[Any] = []

        try:
            for idx, img in enumerate(images):
                # PaddleOCR 3.x doc preprocessor expects RGB (H, W, 3); grayscale causes tuple index out of range.
                img_array = self._pil_to_rgb_array(img)
                # PaddleOCR 3.x: use predict() (ocr() is deprecated and predict() does not accept cls=).
                result = self._ocr.predict(img_array)
                raw_results.append(result)

                page_lines, page_scores = self._parse_ocr_result(result)
                logger.info(
                    "paddleocr_page_processed",
                    page_index=idx,
                    line_count=len(page_lines),
                    avg_confidence=(sum(page_scores) / len(page_scores)) if page_scores else 0.0,
                )
                all_lines.extend(page_lines)
                all_scores.extend(page_scores)

            text = "\n".join(all_lines)
            avg_conf = (sum(all_scores) / len(all_scores)) if all_scores else 0.0

            return {
                "text": text,
                "raw_response": {"paddleocr_result": raw_results},
                "confidence_scores": {"overall": float(avg_conf)},
                "extraction_method": "paddleocr",
            }
        except Exception as e:  # pragma: no cover - defensive
            logger.error("paddleocr_extraction_failed", error=str(e), exc_info=True)
            return {
                "text": "",
                "raw_response": {"error": str(e)},
                "confidence_scores": {},
                "extraction_method": "paddleocr_failed",
            }

    def _pdf_to_images(self, file_content: bytes) -> List[Image.Image]:
        """Convert PDF bytes to a list of PIL Images (first few pages).

        Primary path: pdf2image + Poppler.
        Fallback path: PyMuPDF (fitz) when Poppler/pdf2image is not available.
        """
        # 1) Try pdf2image (Poppler). On Windows, set POPPLER_PATH to the folder containing pdfinfo.exe if not on PATH.
        try:
            from pdf2image import convert_from_bytes  # type: ignore

            poppler_path = os.environ.get("POPPLER_PATH") or None
            if poppler_path and not os.path.isdir(poppler_path):
                poppler_path = None

            images = convert_from_bytes(
                file_content,
                first_page=1,
                last_page=3,
                poppler_path=poppler_path,
            )
            logger.info("pdf_converted_to_images", page_count=len(images), backend="pdf2image")
            return images
        except Exception as e:  # pragma: no cover - Poppler missing or pdf2image failed
            # Only treat known "Poppler not installed / pdfinfo.exe missing" cases as eligible for fallback.
            is_poppler_missing = (
                type(e).__name__ == "PDFInfoNotInstalledError"
                or isinstance(e, FileNotFoundError)
                or (isinstance(e, OSError) and getattr(e, "winerror", None) == 2)
            )
            if is_poppler_missing:
                logger.warning(
                    "pdf_poppler_missing_fallback",
                    error=str(e),
                    backend="pymupdf",
                )
                return self._pdf_to_images_pymupdf(file_content)
            raise

    def _pdf_to_images_pymupdf(self, file_content: bytes) -> List[Image.Image]:
        """Convert PDF to images using PyMuPDF (fitz). No external binaries; works on Windows without Poppler."""
        try:
            import fitz  # type: ignore  # PyMuPDF
        except ImportError:
            logger.error(
                "pymupdf_not_available",
                message="Install pymupdf for PDF support without Poppler: pip install pymupdf",
            )
            raise RuntimeError(
                "PDF conversion failed (Poppler not found). Install Poppler and set POPPLER_PATH, or install pymupdf: pip install pymupdf"
            ) from None

        images: List[Image.Image] = []
        max_pages = 3
        dpi = 200
        doc = fitz.open(stream=file_content, filetype="pdf")
        try:
            for i in range(min(len(doc), max_pages)):
                page = doc[i]
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
        finally:
            doc.close()
        logger.info("pdf_converted_to_images", page_count=len(images), backend="pymupdf")
        return images

    def _pil_to_rgb_array(self, img: Image.Image):
        """Convert PIL image to RGB numpy array (H, W, 3). PaddleOCR 3.x requires 3-channel input for its doc preprocessor."""
        import numpy as np  # type: ignore

        rgb = img.convert("RGB")
        return np.array(rgb)

    def _parse_ocr_result(self, result: Any) -> Tuple[List[str], List[float]]:
        """
        Flatten PaddleOCR result into text lines and confidence scores.

        Supports:
        - Legacy (2.x): list of pages, each page = [ [box, (text, score)], ... ]
        - PaddleOCR 3.x predict(): may return dict with 'rec_texts' / 'rec_scores' or list structure.
        """
        lines: List[str] = []
        scores: List[float] = []

        if result is None:
            return lines, scores

        # PaddleOCR 3.x: result can be a dict (e.g. from pipeline output).
        if isinstance(result, dict):
            rec_texts = result.get("rec_texts") or result.get("texts") or []
            rec_scores = result.get("rec_scores") or result.get("scores") or []
            if isinstance(rec_texts, (list, tuple)):
                for t in rec_texts:
                    lines.append((t or "").strip())
                for s in rec_scores:
                    try:
                        scores.append(float(s))
                    except (TypeError, ValueError):
                        pass
            # Ensure scores length matches lines (pad or trim).
            while len(scores) < len(lines):
                scores.append(0.0)
            return lines, scores[: len(lines)]
        # List structure: PaddleOCR 3.x returns list of per-image results (OCRResult dict-like with rec_texts/rec_scores).
        if isinstance(result, (list, tuple)):
            for page in result:
                if not page:
                    continue
                # 3.x: page may be dict or object with rec_texts / rec_scores.
                rec_texts = None
                rec_scores = None
                if isinstance(page, dict):
                    rec_texts = page.get("rec_texts") or page.get("texts") or page.get("dt_texts")
                    rec_scores = page.get("rec_scores") or page.get("scores")
                elif hasattr(page, "get"):
                    rec_texts = page.get("rec_texts") or page.get("texts") or page.get("dt_texts")
                    rec_scores = page.get("rec_scores") or page.get("scores")
                else:
                    rec_texts = getattr(page, "rec_texts", None) or getattr(page, "texts", None) or getattr(page, "dt_texts", None)
                    rec_scores = getattr(page, "rec_scores", None) or getattr(page, "scores", None)
                if rec_texts is not None and isinstance(rec_texts, (list, tuple)):
                    for t in rec_texts:
                        lines.append((str(t).strip() if t is not None else ""))
                    if rec_scores is not None and isinstance(rec_scores, (list, tuple)):
                        for s in rec_scores:
                            try:
                                scores.append(float(s))
                            except (TypeError, ValueError):
                                pass
                    while len(scores) < len(lines):
                        scores.append(0.0)
                    continue
                # Legacy: page is list of [box, (text, score)] or list of dicts.
                for item in page:
                    try:
                        if isinstance(item, dict):
                            text = (item.get("text") or item.get("rec_text") or "").strip()
                            score = item.get("score", item.get("rec_score", 0.0))
                        else:
                            _, (text, score) = item
                            text = (text or "").strip()
                        if text:
                            lines.append(text)
                            scores.append(float(score))
                    except Exception:
                        continue
            return lines, scores

        return lines, scores


