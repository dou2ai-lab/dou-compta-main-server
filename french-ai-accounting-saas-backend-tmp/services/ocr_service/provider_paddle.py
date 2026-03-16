# -----------------------------------------------------------------------------
# Migrated from french-accounting-ai-saas-ai-pipeline (AI Pipeline repo).
# PaddleOCR provider: image + PDF support.
# -----------------------------------------------------------------------------
"""
PaddleOCR Provider
CPU-friendly OCR using PaddleOCR with optional PDF → image pipeline.

Dependencies (optional): pip install paddlepaddle paddleocr pdf2image opencv-python pillow pymupdf
PDF: Poppler (pdf2image) or PyMuPDF fallback.
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
        try:
            from paddleocr import PaddleOCR  # type: ignore
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="fr",
            )
            logger.info("paddleocr_initialized", engine="PaddleOCR")
        except Exception as e:
            logger.error(
                "paddleocr_init_failed",
                error=str(e),
                message="Install paddlepaddle, paddleocr, pdf2image and opencv-python for PaddleOCR support.",
            )
            self._ocr = None

    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """
        Extract text using PaddleOCR. Handles images and PDFs (first few pages).
        """
        if self._ocr is None:
            logger.warning("paddleocr_not_available", message="Falling back to empty OCR result.")
            return {
                "text": "",
                "ocr_text": "",
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
        except Exception as e:
            logger.error("paddleocr_image_load_failed", error=str(e), mime_type=mime_type, exc_info=True)
            return {
                "text": "",
                "ocr_text": "",
                "raw_response": {"error": f"Failed to load image/PDF: {e}"},
                "confidence_scores": {},
                "extraction_method": "paddleocr_image_load_failed",
            }

        all_lines: List[str] = []
        all_scores: List[float] = []
        raw_results: List[Any] = []

        try:
            for idx, img in enumerate(images):
                img_array = self._pil_to_rgb_array(img)
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
                "ocr_text": text,
                "raw_response": {"paddleocr_result": raw_results},
                "confidence_scores": {"overall": float(avg_conf)},
                "extraction_method": "paddleocr",
            }
        except Exception as e:
            logger.error("paddleocr_extraction_failed", error=str(e), exc_info=True)
            return {
                "text": "",
                "ocr_text": "",
                "raw_response": {"error": str(e)},
                "confidence_scores": {},
                "extraction_method": "paddleocr_failed",
            }

    def _pdf_to_images(self, file_content: bytes) -> List[Image.Image]:
        """Convert PDF bytes to a list of PIL Images. Uses pdf2image (Poppler) or PyMuPDF fallback."""
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
        except Exception as e:
            is_poppler_missing = (
                type(e).__name__ == "PDFInfoNotInstalledError"
                or isinstance(e, FileNotFoundError)
                or (isinstance(e, OSError) and getattr(e, "winerror", None) == 2)
            )
            if is_poppler_missing:
                logger.warning("pdf_poppler_missing_fallback", error=str(e), backend="pymupdf")
                return self._pdf_to_images_pymupdf(file_content)
            raise

    def _pdf_to_images_pymupdf(self, file_content: bytes) -> List[Image.Image]:
        """Convert PDF to images using PyMuPDF (fitz). No external binaries."""
        try:
            import fitz  # type: ignore
        except ImportError:
            logger.error("pymupdf_not_available", message="Install pymupdf for PDF without Poppler: pip install pymupdf")
            raise RuntimeError(
                "PDF conversion failed (Poppler not found). Install Poppler and set POPPLER_PATH, or: pip install pymupdf"
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
        import numpy as np  # type: ignore
        rgb = img.convert("RGB")
        return np.array(rgb)

    def _parse_ocr_result(self, result: Any) -> Tuple[List[str], List[float]]:
        """Flatten PaddleOCR result into text lines and confidence scores. Supports 2.x and 3.x output."""
        lines: List[str] = []
        scores: List[float] = []

        if result is None:
            return lines, scores

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
            while len(scores) < len(lines):
                scores.append(0.0)
            return lines, scores[: len(lines)]

        if isinstance(result, (list, tuple)):
            for page in result:
                if not page:
                    continue
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
