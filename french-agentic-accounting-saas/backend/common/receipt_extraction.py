# -----------------------------------------------------------------------------
# Shared regex-based receipt extraction from OCR text.
# Used by DataNormalizer and receipt_pipeline.
# -----------------------------------------------------------------------------
import re
from datetime import datetime
from typing import Dict


def normalize_amount_str(s: str) -> str:
    """Normalize amount string: French 136,50 -> 136.50; US 1,236.50 -> 1236.50."""
    s = s.strip().replace(" ", "").replace("€", "").replace("$", "").replace("\u00a0", "")
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        parts = s.rsplit(",", 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) <= 2:
            s = parts[0].replace(",", "").replace(" ", "") + "." + parts[1]
        else:
            s = s.replace(",", "")
    return s


def extract_from_ocr_text(ocr_text: str) -> Dict:
    """
    Extract structured data from raw OCR text using regex.
    Supports French: TOTAL TTC, TVA, comma decimals (136,50), Séjour dates.
    Returns dict with total_amount, vat_amount, vat_rate, expense_date, merchant_name.
    """
    result: Dict = {}
    if not ocr_text or not ocr_text.strip():
        return result
    text = ocr_text.strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Total amount
    total_patterns = [
        r"(?:TOTAL\s*TTC|TOTAL TTC|Total TTC|TotalTTC)\s*[:\s]*[$€]?\s*([\d\s,]+[.,]?\d*)",
        r"(?:TOTAL\s*TTC|TOTAL TTC|Total TTC)\s*[:\s]*([\d\s,]+[.,]?\d*)\s*[$€]?",
        r"TTC\s*[:\s]*[$€]?\s*([\d\s,]+[.,]\d{2})",
        r"(?:TOTAL|Total)\s*[:\s]*[$€]?\s*([\d\s,]+[.,]?\d*)",
        r"(?:TOTAL|Total)\s*[:\s]*([\d\s,]+[.,]?\d*)\s*[$€]?",
        r"(?:Amount Due|Amount due|AMOUNT|Montant)\s*[:\s]*[$€]?\s*([\d\s,]+[.,]?\d*)",
    ]
    for pat in total_patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            try:
                result["total_amount"] = float(normalize_amount_str(m.group(1)))
                break
            except (ValueError, IndexError):
                pass

    if "total_amount" not in result:
        amt_matches = re.findall(r"[\d\s,]+[.,]\d{2}(?:\s*[$€])?(?=\s*$)", text, re.MULTILINE)
        if amt_matches:
            try:
                result["total_amount"] = float(normalize_amount_str(amt_matches[-1]))
            except ValueError:
                pass

    # Fallback: largest amount with 2 decimals (e.g. 136,50 or 14,00)
    if "total_amount" not in result:
        all_amounts = re.findall(r"\b(\d{1,4}[.,]\d{2})\b", text)
        valid = []
        for a in all_amounts:
            try:
                v = float(normalize_amount_str(a))
                if 1 < v < 100000:
                    valid.append(v)
            except ValueError:
                pass
        if valid:
            result["total_amount"] = max(valid)

    # VAT rate
    vat_rate_patterns = [
        r"TVA\s*[\(]?\s*(\d+(?:[.,]\d+)?)\s*%?\s*[\)]?",
        r"VAT\s*[\(]?\s*(\d+(?:[.,]\d+)?)\s*%?\s*[\)]?",
    ]
    for pat in vat_rate_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                result["vat_rate"] = float(m.group(1).replace(",", "."))
                break
            except (ValueError, IndexError):
                pass

    # VAT amount
    vat_amt_patterns = [
        r"TVA[^\d]*(?:\d+\s*%[^\d]*)?([\d\s,]+[.,]\d{2})",
        r"TVA\s*(?:\d+%?\s*[-–:])?\s*([\d\s,]+[.,]\d{2})",
        r"VAT[^\d]*(?:\d+\s*%[^\d]*)?([\d\s,]+[.,]\d{2})",
    ]
    for pat in vat_amt_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                result["vat_amount"] = float(normalize_amount_str(m.group(1)))
                break
            except (ValueError, IndexError):
                pass

    # Date
    MONTHS = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
        "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def _parse_month_name_date(month_str: str, day_str: str, year_str: str):
        try:
            m_num = MONTHS.get(month_str.lower())
            if m_num is None:
                return None
            d = int(day_str)
            y = int(year_str)
            dt = datetime(y, m_num, d)
            if 1990 <= dt.year <= 2055 and 1 <= d <= 31:
                return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
        return None

    def _parse_date(g, day_first: bool = False):
        try:
            a, b, c = str(g[0]), str(g[1]), str(g[2])
            if a.lower() in MONTHS:
                return _parse_month_name_date(a, b, c)
            if day_first and b.lower() in MONTHS:
                return _parse_month_name_date(b, a, c)
            if len(a) == 4 and a.isdigit() and 2000 <= int(a) <= 2055:
                y, m_num, d = int(a), int(b), int(c)
            else:
                ai, bi = int(a), int(b)
                y = int(c)
                if len(c) == 2:
                    y = 2000 + y if y < 50 else 1900 + y
                if ai > 12:
                    d, m_num = ai, bi
                elif bi > 12:
                    m_num, d = ai, bi
                else:
                    m_num, d = ai, bi
            dt = datetime(y, m_num, d)
            if 1990 <= dt.year <= 2055 and 1 <= m_num <= 12 and 1 <= d <= 31:
                return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError, TypeError):
            pass
        return None

    date_patterns = [
        (r"(?:Séjour|Sejour|Stay)\s*[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", False),
        (r"(?:Invoice Date|DATE|Date|Issue Date|Invoice date)\s*[:\s]*([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", False),
        (r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", False),
        (r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", True),
        (r"(?:DATE|Date|Invoice Date|Issue Date|Invoice date)\s*[:\s#]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", False),
        (r"(?:INVOICE\s*#?\s*\d*\s*)?(?:DATE|Date)\s*[:\s]*(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", False),
        (r"(?:DATE|Date)\s*[:\s]*(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})", False),
        (r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", False),
        (r"(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})", False),
    ]
    for item in date_patterns:
        pat, day_first = (item[0], item[1]) if isinstance(item, tuple) else (item, False)
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            parsed = _parse_date(m.groups(), day_first=day_first)
            if parsed:
                result["expense_date"] = parsed
                break

    # Merchant
    skip_patterns = (r"\[.*\]", r"^INVOICE$", r"^\d+$", r"^#\d+", r"^BILL TO$", r"^SHIP TO$", r"Thank you", r"^Date", r"^TOTAL", r"^Client$", r"^Séjour$")
    for line in lines[:20]:
        line = " ".join(line.split())
        if len(line) < 2 or len(line) > 60:
            continue
        if any(re.search(p, line, re.I) for p in skip_patterns):
            continue
        if re.match(r"^[\d/\.\-]+$", line):
            continue
        if re.search(r"[a-zA-ZÀ-ÿ]", line) and not re.match(r"^\d+\s+\w+", line):
            result["merchant_name"] = line
            break

    return result
