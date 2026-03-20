# -----------------------------------------------------------------------------
# File: provider_tesseract.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 02-12-2025
# Description: Tesseract OCR provider implementation (free, self-hosted)
# -----------------------------------------------------------------------------

"""
Tesseract OCR Provider
Free, self-hosted OCR solution using pytesseract.
Supports both images and PDFs (PDF → images via pdf2image / PyMuPDF).
"""
import io
import os
from typing import Dict, List, Any, Tuple

import structlog
from PIL import Image
import pytesseract

from .config import settings
from .provider import OCRProvider
from .preprocess import preprocess_pil_image

logger = structlog.get_logger()

class TesseractOCRProvider(OCRProvider):
    """Tesseract OCR provider implementation"""
    
    def __init__(self):
        """Initialize Tesseract OCR provider"""
        # Tesseract should be installed in the system
        # For Docker, it should be in the Dockerfile
        try:
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            logger.info("tesseract_initialized", version=pytesseract.get_tesseract_version())
        except Exception as e:
            logger.warning("tesseract_not_available", error=str(e))
            logger.warning("tesseract_fallback_to_text_extraction", message="Will attempt basic text extraction")
    
    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            file_content: Image file content as bytes
            mime_type: MIME type of file
        
        Returns:
            Dictionary with extracted text and raw OCR data
        """
        logger.info("tesseract_ocr_extraction_started", mime_type=mime_type)
        
        try:
            images: List[Image.Image]
            if mime_type == "application/pdf":
                images = self._pdf_to_images(file_content)
            else:
                images = [Image.open(io.BytesIO(file_content))]

            all_text_parts: List[str] = []
            all_ocr_data: List[Dict] = []
            all_blocks: List[Dict] = []
            all_lines: List[Dict[str, Any]] = []

            for page_index, img in enumerate(images):
                # Preprocess image for better OCR (layout + numbers).
                pre_img = preprocess_pil_image(img, mode="standard")

                def _run_tesseract(target_img: Image.Image) -> tuple[str, Dict]:
                    try:
                        text_out = pytesseract.image_to_string(target_img, lang="fra+eng", config="--psm 6")
                    except Exception:
                        text_out = pytesseract.image_to_string(target_img, lang="eng", config="--psm 6")
                    data_out = pytesseract.image_to_data(target_img, output_type=pytesseract.Output.DICT, config="--psm 6")
                    return text_out, data_out

                ocr_text, ocr_data = _run_tesseract(pre_img)
                cleaned_text = self._clean_ocr_text(ocr_text)

                # Retry once with a more aggressive preprocessing if we got nothing useful.
                if not cleaned_text or len(cleaned_text.strip()) < 10:
                    pre_img2 = preprocess_pil_image(img, mode="aggressive")
                    ocr_text2, ocr_data2 = _run_tesseract(pre_img2)
                    cleaned_text2 = self._clean_ocr_text(ocr_text2)
                    if cleaned_text2 and len(cleaned_text2.strip()) > len((cleaned_text or "").strip()):
                        cleaned_text = cleaned_text2
                        ocr_text = ocr_text2
                        ocr_data = ocr_data2

                if cleaned_text:
                    all_text_parts.append(cleaned_text)

                # Layout-preserving blocks (group by line).
                try:
                    blocks = self._blocks_from_tesseract_data(ocr_data, page_index=page_index)
                    all_blocks.extend(blocks)
                except Exception:
                    pass

                # Line-level structure for label/value alignment downstream.
                try:
                    lines = self._lines_from_tesseract_data(ocr_data, page_index=page_index)
                    all_lines.extend(lines)
                except Exception:
                    pass

                all_ocr_data.append(ocr_data)

            combined_text = "\n\n".join(all_text_parts)

            logger.info(
                "tesseract_ocr_extraction_completed",
                text_length=len(combined_text),
                characters_extracted=len(combined_text.replace('\n', '').replace(' ', '')),
                page_count=len(images),
            )
            
            return {
                "raw_text": combined_text,
                "text": combined_text,
                "blocks": all_blocks,
                "lines": all_lines,
                "raw_response": {
                    "ocr_data": all_ocr_data,
                    "blocks_count": len(all_blocks),
                    "lines_count": len(all_lines),
                    "page_count": len(images),
                },
                "confidence_scores": {},  # Tesseract doesn't provide per-field confidence
                "extraction_method": "tesseract_ocr",
            }
        
        except Exception as e:
            logger.error("tesseract_ocr_extraction_failed", error=str(e), exc_info=True)
            # Return empty text on failure
            return {
                "text": "",
                "raw_response": {"error": str(e)},
                "confidence_scores": {},
                "extraction_method": "tesseract_ocr_failed"
            }
    
    def _pdf_to_images(self, file_content: bytes) -> List[Image.Image]:
        """
        Convert PDF bytes to a list of PIL Images (all pages or first few pages).
        Primary path: pdf2image + Poppler.
        Fallback path: PyMuPDF (fitz) when Poppler/pdf2image is not available.
        """
        # 1) Try pdf2image (Poppler). On macOS, Poppler can be installed via Homebrew.
        try:
            from pdf2image import convert_from_bytes  # type: ignore

            poppler_path = os.environ.get("POPPLER_PATH") or None
            if poppler_path and not os.path.isdir(poppler_path):
                poppler_path = None

            images = convert_from_bytes(
                file_content,
                first_page=1,
                last_page=None,
                poppler_path=poppler_path,
            )
            if not images:
                raise ValueError("PDF produced no images")
            logger.info("tesseract_pdf_converted_to_images", page_count=len(images), backend="pdf2image")
            return images
        except Exception as e:
            logger.warning("tesseract_pdf2image_failed_trying_pymupdf", error=str(e))

        # 2) Fallback: PyMuPDF (fitz), no external binaries needed.
        try:
            import fitz  # type: ignore
        except ImportError:
            logger.error(
                "tesseract_pymupdf_not_available",
                message="Install pymupdf for PDF support without Poppler: pip install pymupdf",
            )
            raise

        images: List[Image.Image] = []
        doc = fitz.open(stream=file_content, filetype="pdf")
        try:
            for i in range(len(doc)):
                page = doc[i]
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
        finally:
            doc.close()

        logger.info("tesseract_pdf_converted_to_images", page_count=len(images), backend="pymupdf")
        return images
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Clean OCR text output
        
        Removes excessive whitespace while preserving structure
        """
        if not text:
            return ""
        
        # Split into lines
        lines = text.split('\n')
        
        # Remove empty lines and excessive whitespace
        cleaned_lines = []
        for line in lines:
            # Strip leading/trailing whitespace
            line = line.strip()
            
            # Skip completely empty lines
            if not line:
                continue
            
            # Fix common OCR errors
            # Replace multiple spaces with single space
            line = ' '.join(line.split())
            
            cleaned_lines.append(line)
        
        # Join with single newline
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        return cleaned_text

    def _blocks_from_tesseract_data(self, data: Dict, *, page_index: int) -> List[Dict]:
        """
        Convert pytesseract image_to_data dict into layout-ish blocks grouped by line.
        Keeps token order; useful for preserving amounts/labels proximity.
        """
        if not isinstance(data, dict) or "text" not in data:
            return []
        n = len(data.get("text") or [])
        blocks_by_line: Dict[tuple, Dict] = {}

        for i in range(n):
            txt = (data["text"][i] or "").strip()
            if not txt:
                continue
            try:
                conf = float(data.get("conf", [])[i])
            except Exception:
                conf = None
            key = (
                page_index,
                data.get("block_num", [0] * n)[i],
                data.get("par_num", [0] * n)[i],
                data.get("line_num", [0] * n)[i],
            )
            left = int(data.get("left", [0] * n)[i] or 0)
            top = int(data.get("top", [0] * n)[i] or 0)
            width = int(data.get("width", [0] * n)[i] or 0)
            height = int(data.get("height", [0] * n)[i] or 0)

            b = blocks_by_line.get(key)
            if not b:
                b = {
                    "page_index": page_index,
                    "text": txt,
                    "tokens": [txt],
                    "bbox": [left, top, left + width, top + height],
                    "confidence": conf,
                }
                blocks_by_line[key] = b
            else:
                b["tokens"].append(txt)
                b["text"] = " ".join(b["tokens"])
                x1, y1, x2, y2 = b["bbox"]
                b["bbox"] = [min(x1, left), min(y1, top), max(x2, left + width), max(y2, top + height)]
                if conf is not None:
                    if b["confidence"] is None:
                        b["confidence"] = conf
                    else:
                        b["confidence"] = float(b["confidence"]) * 0.9 + conf * 0.1

        # Stable order: by page, then y, then x.
        out = list(blocks_by_line.values())
        out.sort(key=lambda b: (b.get("page_index", 0), (b.get("bbox") or [0, 0, 0, 0])[1], (b.get("bbox") or [0, 0, 0, 0])[0]))
        return out

    def _lines_from_tesseract_data(self, data: Dict, *, page_index: int) -> List[Dict[str, Any]]:
        """
        Convert pytesseract image_to_data output into line-level structures.

        Output format (required by pipeline):
        meta_data.ocr.lines = [{ text, tokens, bbox: [left, top, right, bottom], line_num, block_num }]
        """
        if not isinstance(data, dict) or "text" not in data:
            return []

        n = len(data.get("text") or [])
        if n == 0:
            return []

        lines_by_key: Dict[Tuple[int, int, int], Dict[str, Any]] = {}

        for i in range(n):
            txt = (data.get("text", [])[i] or "").strip()
            if not txt:
                continue            block_num = int((data.get("block_num", [0] * n)[i] or 0) or 0)
            par_num = int((data.get("par_num", [0] * n)[i] or 0) or 0)
            line_num = int((data.get("line_num", [0] * n)[i] or 0) or 0)

            left = int((data.get("left", [0] * n)[i] or 0) or 0)
            top = int((data.get("top", [0] * n)[i] or 0) or 0)
            width = int((data.get("width", [0] * n)[i] or 0) or 0)
            height = int((data.get("height", [0] * n)[i] or 0) or 0)
            right = left + width
            bottom = top + height

            key = (block_num, par_num, line_num)
            bucket = lines_by_key.get(key)
            if not bucket:
                lines_by_key[key] = {
                    "page_index": page_index,
                    "block_num": block_num,
                    "par_num": par_num,
                    "line_num": line_num,
                    "tokens": [(left, txt)],
                    "text": txt,
                    "bbox": [left, top, right, bottom],
                }
            else:
                bucket["tokens"].append((left, txt))
                x1, y1, x2, y2 = bucket["bbox"]
                bucket["bbox"] = [min(x1, left), min(y1, top), max(x2, right), max(y2, bottom)]

        out = []
        for _, bucket in lines_by_key.items():
            # Stable within-line order: left → right
            bucket["tokens"].sort(key=lambda t: t[0])
            tokens_txt = [t[1] for t in bucket.get("tokens") or []]
            bucket["text"] = " ".join(tokens_txt).strip()
            bucket["tokens"] = tokens_txt
            out.append(bucket)

        # Reading order: top → left (then page)
        out.sort(
            key=lambda l: (
                l.get("page_index", 0),
                (l.get("bbox") or [0, 0, 0, 0])[1],
                (l.get("bbox") or [0, 0, 0, 0])[0],
            )
        )
        return out