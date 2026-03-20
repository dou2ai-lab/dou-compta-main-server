# -----------------------------------------------------------------------------
# In-process receipt pipeline when RabbitMQ is not available.
# Runs OCR -> normalize -> LLM extract -> update receipt -> create expense.
# -----------------------------------------------------------------------------
import asyncio
import uuid as uuid_lib
from datetime import datetime
from decimal import Decimal
import io
from typing import Optional
import time
import re
from sqlalchemy import select
from sqlalchemy.orm import attributes
import structlog

from common.database import AsyncSessionLocal
from common.models import Expense
from common.receipt_extraction import extract_from_ocr_text
from .models import ReceiptDocument
from .storage import StorageService
from .encryption import EncryptionService
from .config import settings

logger = structlog.get_logger()


def _extract_from_ocr_text(ocr_text: str) -> dict:
    """Delegate to shared extraction module."""
    return extract_from_ocr_text(ocr_text)


def _compute_overall_confidence(confidence_scores: dict) -> Optional[float]:
    if not isinstance(confidence_scores, dict) or not confidence_scores:
        return None
    vals = []
    for v in confidence_scores.values():
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if 0.0 <= fv <= 1.0:
            vals.append(fv)
    if not vals:
        return None
    return sum(vals) / len(vals)


def _apply_prd_validation(extraction_dict: dict) -> dict:
    """
    Apply PRD rules:
    - Critical fields: total_amount, expense_date
    - If missing critical -> REQUIRES_MANUAL_VALIDATION
    - If confidence < 0.97 -> needs_review
    - If confidence < 0.60 -> rejected
    """
    if not extraction_dict:
        return extraction_dict

    total_amount = extraction_dict.get("total_amount")
    expense_date = extraction_dict.get("expense_date")

    critical_missing = total_amount in (None, "", 0) or expense_date in (None, "")
    if critical_missing:
        extraction_dict["status"] = "REQUIRES_MANUAL_VALIDATION"
        extraction_dict.setdefault("validation_flags", [])
        if total_amount in (None, "", 0):
            extraction_dict["validation_flags"].append("missing_total_amount")
        if expense_date in (None, ""):
            extraction_dict["validation_flags"].append("missing_expense_date")

    overall = extraction_dict.get("overall_confidence")
    if overall is None:
        overall = _compute_overall_confidence(extraction_dict.get("confidence_scores") or {})
        extraction_dict["overall_confidence"] = overall

    if overall is not None:
        try:
            overall_f = float(overall)
        except (TypeError, ValueError):
            overall_f = None
        if overall_f is not None:
            if overall_f < 0.60:
                extraction_dict["status"] = "rejected"
            elif overall_f < 0.97 and extraction_dict.get("status") is None:
                extraction_dict["status"] = "needs_review"
            elif extraction_dict.get("status") is None:
                extraction_dict["status"] = "completed"

    if extraction_dict.get("status") is None:
        extraction_dict["status"] = "completed" if not critical_missing else extraction_dict["status"]

    return extraction_dict


def _append_meta_error(meta: dict, *, step: str, error: str) -> None:
    if meta is None:
        return
    errs = meta.get("pipeline_errors")
    if not isinstance(errs, list):
        errs = []
        meta["pipeline_errors"] = errs
    errs.append({"step": step, "error": error})


def _value_evidence_in_text(value: object, ocr_text: str) -> bool:
    """Heuristic: check if a value appears in OCR text (handles comma/dot decimals)."""
    if value is None or not ocr_text:
        return False
    s = str(value).strip()
    if not s:
        return False
    t = ocr_text.lower()
    s_low = s.lower()
    if s_low in t:
        return True
    # Handle decimal normalization (597.6 vs "597,60")
    if "." in s_low:
        s_comma = s_low.replace(".", ",")
        if s_comma in t:
            return True
    if "," in s_low:
        s_dot = s_low.replace(",", ".")
        if s_dot in t:
            return True
    return False


def _parse_amount_from_match(m: str) -> Optional[float]:
    if m is None:
        return None
    s = str(m).strip()
    if not s:
        return None
    s = (
        s.replace("€", "")
        .replace("EUR", "")
        .replace("$", "")
        .replace("USD", "")
        .replace("\u00a0", " ")
    )
    s = s.replace(" ", "")
    # Normalize thousand separators/decimal separators (French-style).
    if "," in s and "." in s:
        # Assume commas are thousands separators.
        s = s.replace(",", "")
    elif "," in s and "." not in s:
        # Comma is decimal separator.
        s = s.replace(",", ".")
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _extract_amount_candidates(line_text: str) -> list[dict]:
    """
    Returns: [{value: float, start: int, end: int, raw: str}, ...]
    Prefer decimals when available.
    """
    if not line_text:
        return []
    # Match amounts like "597,60" or "199.00" and also integers.
    pattern = r"(-?\d[\d\s\u00a0]*[.,]\d{2}|-?\d[\d\s\u00a0]*)"
    candidates: list[dict] = []
    for m in re.finditer(pattern, line_text):
        raw = m.group(1)
        val = _parse_amount_from_match(raw)
        if val is None:
            continue
        # Heuristic: keep reasonable monetary ranges.
        if -1e9 <= val <= 1e9:
            candidates.append({"value": val, "start": m.start(1), "end": m.end(1), "raw": raw})
    return candidates


def _deterministic_vendor_from_lines(lines: list[dict]) -> tuple[Optional[str], dict]:
    """
    Vendor name extraction:
    Prefer: Vendor:, Fournisseur:, Company:
    Reject: Invoice Number, Date, Total, VAT
    """
    debug: dict = {"vendor_candidates": [], "rejected": []}
    if not isinstance(lines, list) or not lines:
        return None, debug

    # Scan only the top portion (common on invoices).
    top_lines = lines[:40]
    patterns = [
        r"\bVENDOR\s*[:\-]\s*(.+)$",
        r"\bFOURNISSEUR\s*[:\-]\s*(.+)$",
        r"\bCOMPANY\s*[:\-]\s*(.+)$",
    ]
    reject_pat = re.compile(r"\b(INVOICE\s*NUMBER|DATE|TOTAL(\s+DUE)?|VAT|TVA)\b", re.IGNORECASE)

    for ln in top_lines:
        if not isinstance(ln, dict):
            continue
        t = str(ln.get("text") or "").strip()
        if not t:
            continue
        for p in patterns:
            m = re.search(p, t, flags=re.IGNORECASE)
            if not m:
                continue
            candidate = m.group(1).strip()
            candidate = " ".join(candidate.split())
            debug["vendor_candidates"].append({"candidate": candidate, "source_line": t})
            if not candidate or reject_pat.search(candidate):
                debug["rejected"].append({"candidate": candidate, "reason": "rejected_pattern"})
                continue
            # Reject values that look like labels-only.
            if candidate.upper() in ("TOTAL", "VAT", "DATE"):
                debug["rejected"].append({"candidate": candidate, "reason": "label_only"})
                continue
            # Reject digit-only.
            if re.fullmatch(r"\d+", candidate):
                debug["rejected"].append({"candidate": candidate, "reason": "digits_only"})
                continue
            return candidate, debug

    return None, debug


def _deterministic_vendor_from_text(ocr_text: str) -> tuple[Optional[str], dict]:
    """
    Vendor name extraction from flat OCR text as a fallback when bbox lines are missing.
    Prefer: Vendor:, Fournisseur:, Company:
    Reject: Invoice Number, Date, Total, VAT
    """
    debug: dict = {"text_vendor_candidates": [], "rejected": []}
    if not ocr_text:
        return None, debug

    # When OCR squashes multiple labels on the same line, we should extract only the
    # vendor token(s) before the next label (e.g. "Vendor: PayFit Invoice Number: ...").
    reject_pat = re.compile(r"\b(INVOICE\s*NUMBER|DATE|TOTAL(\s+DUE)?|VAT|TVA)\b", re.IGNORECASE)
    stop_at_pat = re.compile(r"\b(INVOICE\s*NUMBER|WEBSITE|SUPPORT|DATE|TOTAL(\s+DUE)?|VAT|TVA)\b", re.IGNORECASE)
    patterns = [
        re.compile(r"\bVENDOR\s*[:\-]\s*(.+)$", re.IGNORECASE),
        re.compile(r"\bFOURNISSEUR\s*[:\-]\s*(.+)$", re.IGNORECASE),
        re.compile(r"\bCOMPANY\s*[:\-]\s*(.+)$", re.IGNORECASE),
    ]

    for raw_line in str(ocr_text).splitlines():
        t = (raw_line or "").strip()
        if not t:
            continue
        for rx in patterns:
            m = rx.search(t)
            if not m:
                continue
            candidate = m.group(1).strip()
            candidate = " ".join(candidate.split())
            # Truncate at the next known label if multiple labels are merged on one line.
            # Keep only the prefix before "Invoice Number:", "Website:", etc.
            stop_m = stop_at_pat.search(candidate)
            if stop_m:
                candidate = candidate[: stop_m.start()].strip()
            debug["text_vendor_candidates"].append({"candidate": candidate, "source_line": t})
            if not candidate or reject_pat.search(candidate):
                debug["rejected"].append({"candidate": candidate, "reason": "rejected_pattern"})
                continue
            if candidate.upper() in ("TOTAL", "VAT", "DATE"):
                debug["rejected"].append({"candidate": candidate, "reason": "label_only"})
                continue
            # Avoid returning obvious label fragments.
            return candidate, debug

    return None, debug


def _fallback_invoice_amounts_from_ocr_text(ocr_text: str) -> tuple[dict, dict]:
    """
    Fallback critical extraction from flat OCR text (no bbox lines available).

    Heuristic for invoices where labels are stacked and amounts appear below:
    - If "TOTAL DUE" exists, take:
      - last amount after TOTAL DUE  => total_amount
      - second last amount           => vat_amount
      - third last amount           => subtotal
    """
    debug: dict = {"text_fallback": None, "amounts_after_total_due": []}
    if not ocr_text:
        return {}, debug

    lines = [ln.strip() for ln in str(ocr_text).splitlines() if (ln or "").strip()]
    total_due_re = re.compile(r"\bTOTAL\s*DUE\b", re.IGNORECASE)

    due_indices = [i for i, ln in enumerate(lines) if total_due_re.search(ln)]
    if not due_indices:
        return {}, debug

    due_idx = max(due_indices)
    # Extract monetary amounts after the TOTAL DUE label.
    amounts: list[dict] = []
    for j in range(due_idx + 1, len(lines)):
        ln = lines[j]
        cands = _extract_amount_candidates(ln)
        for c in cands:
            raw = (c.get("raw") or "").replace("\u00a0", " ").strip()
            # Filter to decimal-like money values to avoid matching date pieces.
            if not re.search(r"[.,]\d{2}", raw):
                continue
            amounts.append({"value": float(c["value"]), "raw": raw, "line_idx": j, "line_text": ln})

    debug["amounts_after_total_due"] = amounts[-10:]  # keep debug compact
    if len(amounts) < 3:
        return {}, debug

    subtotal = amounts[-3]["value"]
    vat_amount = amounts[-2]["value"]
    total_amount = amounts[-1]["value"]

    out: dict = {
        "subtotal": round(float(subtotal), 2),
        "vat_amount": round(float(vat_amount), 2),
        "total_amount": round(float(total_amount), 2),
    }
    if out["subtotal"]:
        out["vat_rate"] = round(float(out["vat_amount"]) / float(out["subtotal"]) * 100.0, 4)

    debug["text_fallback"] = {
        "chosen": out,
        "note": "Heuristic: last 3 money values after TOTAL DUE",
    }
    return out, debug


def _deterministic_label_value_mapping(lines: list[dict]) -> tuple[dict, dict]:
    """
    Deterministic label-value alignment for:
    - TOTAL DUE -> total_amount
    - VAT -> vat_amount
    - TOTAL or SUBTOTAL -> subtotal

    Uses line bbox proximity:
    - same line if numeric exists
    - else nearest line below within vertical threshold and closest left (column-ish).
    """
    debug: dict = {"detected_labels": [], "label_candidates": {}, "rejected": []}
    if not isinstance(lines, list) or not lines:
        return {}, debug

    # Filter to dict lines with bbox.
    line_objs: list[dict] = []
    for ln in lines:
        if not isinstance(ln, dict):
            continue
        bbox = ln.get("bbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            continue
        if not ln.get("text"):
            continue
        line_objs.append(ln)

    def _line_text(ln: dict) -> str:
        return str(ln.get("text") or "").strip()

    # Label detection
    label_regex = {
        "total_due": re.compile(r"\bTOTAL\s*DUE\b", re.IGNORECASE),
        "vat": re.compile(r"\bVAT\b|\bTVA\b", re.IGNORECASE),
        "subtotal": re.compile(r"\bSUBTOTAL\b|SOUS[-\s]?TOTAL", re.IGNORECASE),
        "total": re.compile(r"\bTOTAL\b", re.IGNORECASE),
    }

    vertical_threshold = 90
    horizontal_threshold = 180

    label_occurrences: dict[str, list[dict]] = {k: [] for k in label_regex.keys()}

    for ln in line_objs:
        t = _line_text(ln)
        if not t:
            continue
        for label, rx in label_regex.items():
            if label == "total" and label_regex["total_due"].search(t):
                # Avoid counting TOTAL DUE as TOTAL.
                continue
            if rx.search(t):
                label_occurrences[label].append(ln)
                debug["detected_labels"].append({"label": label, "text": t, "bbox": ln.get("bbox")})

    def _choose_nearest_numeric(label_line: dict) -> tuple[Optional[float], dict]:
        """
        Returns (value, detail_debug)
        """
        out_detail = {"label_bbox": label_line.get("bbox"), "candidates": [], "chosen": None, "rejected": []}
        label_text = _line_text(label_line)
        label_left = (label_line.get("bbox") or [0, 0, 0, 0])[0]
        label_bottom = (label_line.get("bbox") or [0, 0, 0, 0])[3]
        # Same-line candidates
        same_candidates = _extract_amount_candidates(label_text)
        if same_candidates:
            # If label_text includes multiple numbers, choose closest to label substring end.
            # Approximation: choose rightmost amount in the line (common for totals).
            same_candidates_sorted = sorted(same_candidates, key=lambda c: c["end"])
            chosen = same_candidates_sorted[-1]
            out_detail["candidates"] = same_candidates_sorted
            out_detail["chosen"] = chosen
            if len(same_candidates_sorted) > 1:
                out_detail["rejected"] = same_candidates_sorted[:-1]
            return chosen["value"], out_detail

        # Otherwise search next lines below within vertical threshold.
        candidates_lines: list[dict] = []
        for ln2 in line_objs:
            bbox2 = ln2.get("bbox") or [0, 0, 0, 0]
            page_ok = True
            if "page_index" in label_line and "page_index" in ln2:
                page_ok = label_line.get("page_index") == ln2.get("page_index")
            if not page_ok:
                continue
            top2 = bbox2[1]
            delta_y = top2 - label_bottom
            if 0 < delta_y <= vertical_threshold:
                candidates_lines.append(ln2)

        # Score numeric candidates by (delta_y, delta_x)
        scored: list[tuple[float, float, dict]] = []
        for ln2 in candidates_lines:
            t2 = _line_text(ln2)
            nums = _extract_amount_candidates(t2)
            if not nums:
                continue
            # take last amount on that line (often the amount at end)
            nums_sorted = sorted(nums, key=lambda c: c["end"])
            chosen_num = nums_sorted[-1]
            bbox2 = ln2.get("bbox") or [0, 0, 0, 0]
            delta_y = bbox2[1] - label_bottom
            delta_x = abs((bbox2[0] or 0) - (label_left or 0))

            # prefer same column
            col_bonus = 0.0 if delta_x <= horizontal_threshold else 200.0
            score_y = float(delta_y)
            score_x = float(delta_x)
            scored.append((score_y + col_bonus, score_x, {"line": ln2, "num": chosen_num, "delta_y": delta_y, "delta_x": delta_x}))

        scored.sort(key=lambda x: x[0])
        if not scored:
            return None, out_detail
        best = scored[0][2]
        out_detail["candidates"] = [{"line_text": _line_text(best["line"]), **best["num"], "delta_y": best["delta_y"], "delta_x": best["delta_x"]}]
        out_detail["chosen"] = best["num"]
        if len(scored) > 1:
            # Mark non-winning numeric candidates as rejected for debug.
            rejected_nums = [s[2]["num"] for s in scored[1:] if isinstance(s[2], dict)]
            out_detail["rejected"] = rejected_nums
        return best["num"]["value"], out_detail

    mapped: dict = {}
    label_debug_details: dict = {}

    # Choose best occurrences for each label type by taking the lowest (closest to bottom).
    def _pick_best_occ(label: str) -> Optional[dict]:
        occs = label_occurrences.get(label) or []
        if not occs:
            return None
        # choose the one with max bbox top (lowest on page) for totals-like fields
        return sorted(occs, key=lambda l: (l.get("bbox") or [0, 0, 0, 0])[1], reverse=True)[0]

    total_due_line = _pick_best_occ("total_due")
    vat_line = _pick_best_occ("vat")
    subtotal_line = _pick_best_occ("subtotal")
    total_line = _pick_best_occ("total")

    # Arithmetic assignment for noisy layouts:
    # If TOTAL DUE exists, choose {subtotal, VAT, total_due} that satisfy:
    #   subtotal + VAT ≈ TOTAL_DUE
    # This prevents picking the first number under the label when other numbers exist.
    if total_due_line and vat_line and total_line:
        try:
            due_bbox = total_due_line.get("bbox") or [0, 0, 0, 0]
            vat_bbox = vat_line.get("bbox") or [0, 0, 0, 0]
            total_bbox = total_line.get("bbox") or [0, 0, 0, 0]

            min_top = min(due_bbox[1], vat_bbox[1], total_bbox[1]) - vertical_threshold
            max_bottom = max(due_bbox[3], vat_bbox[3], total_bbox[3]) + vertical_threshold

            candidates_occ: list[dict] = []
            for ln in line_objs:
                bbox = ln.get("bbox") or [0, 0, 0, 0]
                top = bbox[1]
                bottom = bbox[3]
                if top < min_top or top > max_bottom:
                    continue
                line_text = _line_text(ln)
                nums = _extract_amount_candidates(line_text)
                if not nums:
                    continue
                for num in nums:
                    candidates_occ.append({
                        "value": float(num["value"]),
                        "bbox": bbox,
                        "line_text": line_text,
                        "delta_to_total_due": abs(top - due_bbox[3]),
                        "delta_to_vat": abs(top - vat_bbox[3]),
                        "delta_to_total": abs(top - total_bbox[3]),
                        "raw": num.get("raw"),
                    })

            # De-duplicate by value (keep best proximity info).
            by_val: dict[float, dict] = {}
            for occ in candidates_occ:
                v = round(float(occ["value"]), 2)
                if v not in by_val:
                    by_val[v] = occ
                else:
                    # Prefer smaller sum of deltas.
                    prev = by_val[v]
                    prev_score = float(prev["delta_to_total_due"]) + float(prev["delta_to_vat"])
                    new_score = float(occ["delta_to_total_due"]) + float(occ["delta_to_vat"])
                    if new_score < prev_score:
                        by_val[v] = occ

            values_sorted = sorted(by_val.keys())
            debug["arithmetic_candidates_values"] = values_sorted

            tol = 0.02
            best_choice = None
            # Try all pairs (subtotal, VAT) and check if total_due exists.
            for net_val in values_sorted:
                if net_val is None or net_val <= 0:
                    continue
                for vat_val in values_sorted:
                    if vat_val is None or vat_val <= 0:
                        continue
                    gross = net_val + vat_val
                    gross_match = None
                    for v2 in values_sorted:
                        if abs(v2 - gross) <= tol:
                            gross_match = v2
                            break
                    if gross_match is None:
                        continue

                    net_occ = by_val.get(round(net_val, 2))
                    vat_occ = by_val.get(round(vat_val, 2))
                    gross_occ = by_val.get(round(gross_match, 2))
                    if not net_occ or not vat_occ or not gross_occ:
                        continue

                    # Score by proximity to label boxes.
                    score = (
                        float(gross_occ["delta_to_total_due"])
                        + float(vat_occ["delta_to_vat"])
                        + float(net_occ["delta_to_total"]) * 0.2
                    )
                    choice = {
                        "subtotal": net_val,
                        "vat_amount": vat_val,
                        "total_amount": gross_match,
                        "score": score,
                        "net_raw": net_occ.get("raw"),
                        "vat_raw": vat_occ.get("raw"),
                        "due_raw": gross_occ.get("raw"),
                    }
                    if best_choice is None:
                        best_choice = choice
                    else:
                        # Prefer lower score; tie-breaker by larger gross.
                        if score < best_choice["score"] or (
                            abs(score - best_choice["score"]) <= 1e-6 and gross_match > best_choice["total_amount"]
                        ):
                            best_choice = choice

            if best_choice is not None:
                mapped.update({
                    "subtotal": round(float(best_choice["subtotal"]), 2),
                    "vat_amount": round(float(best_choice["vat_amount"]), 2),
                    "total_amount": round(float(best_choice["total_amount"]), 2),
                })
                if mapped["subtotal"] and mapped["subtotal"] != 0:
                    mapped["vat_rate"] = mapped["vat_amount"] / mapped["subtotal"] * 100.0
                debug["arithmetic_assignment"] = {
                    "chosen": best_choice,
                    "note": "Chosen to satisfy subtotal + VAT ≈ TOTAL_DUE",
                }
                return mapped, debug
        except Exception as e:
            logger.warning("arithmetic_assignment_failed", receipt_id=receipt_id, error=str(e))

    if total_due_line:
        v, d = _choose_nearest_numeric(total_due_line)
        label_debug_details["total_due"] = d
        mapped["total_amount"] = v
    if vat_line:
        v, d = _choose_nearest_numeric(vat_line)
        label_debug_details["vat"] = d
        mapped["vat_amount"] = v

    # Subtotal: prefer SUBTOTAL label; else TOTAL (when TOTAL DUE exists).
    if subtotal_line:
        v, d = _choose_nearest_numeric(subtotal_line)
        label_debug_details["subtotal"] = d
        mapped["subtotal"] = v
    elif total_due_line and total_line:
        v, d = _choose_nearest_numeric(total_line)
        label_debug_details["total_as_subtotal"] = d
        mapped["subtotal"] = v

    # Derive VAT rate if possible (subtotal is net, total is gross).
    if mapped.get("vat_amount") is not None and mapped.get("subtotal") not in (None, 0):
        try:
            mapped["vat_rate"] = float(mapped["vat_amount"]) / float(mapped["subtotal"]) * 100.0
        except Exception:
            mapped["vat_rate"] = None

    debug["label_candidates"] = label_debug_details
    return mapped, debug


def _enhance_confidence_and_audit(ext_dict: dict, *, ocr_text: str, ocr_confidence: Optional[float]) -> dict:
    """
    Combine OCR evidence + LLM confidence + basic validation into field-level confidence.
    Also store per-field sources + brief reasoning for auditability.
    """
    if not ext_dict:
        return ext_dict

    conf: dict = ext_dict.get("confidence_scores") or {}
    sources: dict = ext_dict.get("field_sources") or {}
    reasoning: dict = ext_dict.get("field_reasoning") or {}

    def set_field(field: str, base: Optional[float], src: str, reason: str) -> None:
        if base is None:
            return
        base = max(0.0, min(1.0, float(base)))
        if ocr_confidence is not None:
            try:
                oc = float(ocr_confidence)
            except (TypeError, ValueError):
                oc = None
            if oc is not None and 0.0 <= oc <= 1.0:
                # Blend a little OCR overall into field score.
                base = min(1.0, (base * 0.85) + (oc * 0.15))
        conf[field] = round(base, 3)
        sources[field] = src
        reasoning[field] = reason

    # Determine doc type and fields to score.
    doc_type = ext_dict.get("document_type") or "autre"

    if doc_type in ("facture_achat", "facture_vente"):
        for field in ("merchant_name", "invoice_number", "expense_date", "total_amount", "vat_amount", "vat_rate", "currency"):
            v = ext_dict.get(field)
            llm_c = conf.get(field)
            has_val = v not in (None, "", 0)
            evidence = _value_evidence_in_text(v, ocr_text) if has_val else False

            if not has_val:
                set_field(field, 0.2, "missing", "Value missing")
            elif evidence and llm_c is not None:
                set_field(field, max(float(llm_c), 0.97), "mixed", "Found in OCR text and extracted by LLM")
            elif evidence:
                set_field(field, 0.85, "ocr", "Found in OCR text")
            elif llm_c is not None:
                set_field(field, float(llm_c), "llm", "Extracted by LLM")
            else:
                set_field(field, 0.65, "regex", "Heuristic extraction (no LLM confidence)")

    elif doc_type == "releve_bancaire":
        bs = ext_dict.get("bank_statement") or {}
        tx = bs.get("transactions") if isinstance(bs, dict) else None
        set_field("bank_statement", 0.85 if tx else 0.5, "llm" if tx else "heuristic", "Bank statement structure extracted")
        # Invoice fields are not critical here; keep low if present without evidence.
        for field in ("total_amount", "expense_date"):
            if ext_dict.get(field) not in (None, "", 0):
                set_field(field, 0.4, "llm", "Invoice field on bank statement (usually not applicable)")

    elif doc_type == "bulletin_paie":
        ps = ext_dict.get("payslip") or {}
        net = ps.get("net_pay") if isinstance(ps, dict) else None
        set_field("payslip", 0.9 if net else 0.6, "llm" if net else "heuristic", "Payslip structure extracted")

    # Overall confidence: average of known numeric field confidences (fallback).
    if ext_dict.get("overall_confidence") is None:
        vals = []
        for k, v in conf.items():
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if 0.0 <= fv <= 1.0:
                vals.append(fv)
        ext_dict["overall_confidence"] = round(sum(vals) / len(vals), 3) if vals else None

    ext_dict["confidence_scores"] = conf
    ext_dict["field_sources"] = sources
    ext_dict["field_reasoning"] = reasoning
    return ext_dict
def _log_pipeline_step(step: str, receipt_id: str, error: str = None, extra: dict = None):
    """Log pipeline step for debugging (and optionally to debug.log)."""
    data = {"receipt_id": receipt_id, "step": step}
    if error:
        data["error"] = error
    if extra:
        data.update(extra)
    logger.info("receipt_pipeline_step", **data)
    try:
        import json
        import time
        path = getattr(settings, "DEBUG_LOG_PATH", None) or r"e:\French Accounting SAAS\.cursor\debug.log"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "message": "pipeline_step",
                "data": data,
                "timestamp": int(time.time() * 1000),
            }) + "\n")
    except Exception:
        pass


def _pdf_to_image_bytes_list(file_content: bytes) -> list[bytes]:
    """
    Convert a PDF into a list of PNG image bytes (one per page).

    Primary path: pdf2image + Poppler.
    Fallback path: PyMuPDF (fitz) to avoid external binaries when available.
    """
    # 1) pdf2image (requires Poppler installed)
    try:
        from pdf2image import convert_from_bytes  # type: ignore
        import os

        poppler_path = os.environ.get("POPPLER_PATH") or None
        if poppler_path and not os.path.isdir(poppler_path):
            poppler_path = None

        images = convert_from_bytes(
            file_content,
            first_page=1,
            last_page=None,
            poppler_path=poppler_path,
        )
        out: list[bytes] = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            out.append(buf.getvalue())
        if not out:
            raise ValueError("PDF produced no images")
        logger.info("receipt_pipeline_pdf_converted", backend="pdf2image", page_count=len(out))
        return out
    except Exception as e:
        logger.warning("receipt_pipeline_pdf2image_failed_trying_pymupdf", error=str(e))

    # 2) PyMuPDF (no external binaries)
    try:
        import fitz  # type: ignore
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "PDF upload requires either Poppler (pdf2image) or PyMuPDF. "
            "Install one of: `brew install poppler` (macOS) + `pip install pdf2image`, "
            "or `pip install pymupdf`."
        ) from e

    doc = fitz.open(stream=file_content, filetype="pdf")
    try:
        out: list[bytes] = []
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            out.append(buf.getvalue())
        if not out:
            raise ValueError("PDF produced no images")
        logger.info("receipt_pipeline_pdf_converted", backend="pymupdf", page_count=len(out))
        return out
    finally:
        doc.close()


def convert_pdf_to_images(file_bytes: bytes):
    """
    Convert PDF bytes to a list of PIL images using pdf2image.
    This is used to guarantee OCR always receives image data (never raw PDF bytes).
    """
    try:
        from pdf2image import convert_from_bytes  # type: ignore

        return convert_from_bytes(file_bytes, first_page=1, last_page=None)
    except Exception as e1:
        # Apple Silicon (macOS/Homebrew) fallback poppler path
        try:
            from pdf2image import convert_from_bytes  # type: ignore

            return convert_from_bytes(
                file_bytes,
                first_page=1,
                last_page=None,
                poppler_path="/opt/homebrew/bin",
            )
        except Exception:
            # Final pure-Python fallback to keep PDF OCR working without Poppler.
            try:
                import fitz  # type: ignore
                from PIL import Image

                doc = fitz.open(stream=file_bytes, filetype="pdf")
                images = []
                try:
                    for i in range(len(doc)):
                        page = doc[i]
                        pix = page.get_pixmap(dpi=200)
                        images.append(
                            Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        )
                finally:
                    doc.close()
                return images
            except Exception:
                # Re-raise original error to keep the root cause visible
                raise e1


async def run_receipt_pipeline(
    receipt_id: str,
    tenant_id: str,
    user_id: str,
    file_metadata: dict,
) -> None:
    """
    Run OCR -> normalize -> LLM extract -> save -> create expense.
    Use when message queue is not available.
    """
    _log_pipeline_step("start", receipt_id)
    started = time.time()
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ReceiptDocument).where(
                    ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                    ReceiptDocument.deleted_at.is_(None),
                )
            )
            receipt = result.scalar_one_or_none()
            if not receipt:
                logger.warning("receipt_not_found", receipt_id=receipt_id)
                return
            try:
                receipt.ocr_status = "processing"
                await db.commit()
            except Exception:
                pass

            storage = StorageService()
            encryption_svc = EncryptionService()

            # Step 1: Download file
            try:
                storage_path = file_metadata.get("storage_path")
                if not storage_path:
                    raise ValueError("file_metadata.storage_path is missing")
                file_content = await storage.download_file(storage_path)
                if not file_content or len(file_content) == 0:
                    raise ValueError("Downloaded file is empty")
                _log_pipeline_step("download_ok", receipt_id, extra={"size": len(file_content)})
            except Exception as e:
                _log_pipeline_step("download_failed", receipt_id, error=str(e))
                raise

            if file_metadata.get("encryption_key_id") and settings.ENCRYPTION_ENABLED:
                try:
                    file_content = await encryption_svc.decrypt(
                        file_content, file_metadata["encryption_key_id"]
                    )
                except Exception as e:
                    logger.error("decrypt_failed", receipt_id=receipt_id, error=str(e))
                    receipt.ocr_status = "failed"
                    if not receipt.meta_data:
                        receipt.meta_data = {}
                    receipt.meta_data["pipeline_error"] = f"Decrypt failed: {e}"
                    attributes.flag_modified(receipt, "meta_data")
                    await db.commit()
                    return

            # Step 2: OCR (convert PDF to image first so Tesseract/Paddle get image bytes)
            try:
                from services.ocr_service.provider import get_ocr_provider
                from services.ocr_service.normalizer import DataNormalizer

                mime_type = file_metadata.get("mime_type") or "image/png"
                mime_type_norm = str(mime_type).strip().lower()
                provider = get_ocr_provider()
                normalizer = DataNormalizer()
                if mime_type_norm == "application/pdf" or mime_type_norm.endswith("/pdf"):
                    # Convert PDF → images and OCR each page, then combine.
                    images = convert_pdf_to_images(file_content)
                    print("PDF pages:", len(images))
                    if len(images) == 0:
                        print("PDF conversion failed (no pages rendered)")
                        logger.warning("receipt_pipeline_pdf_conversion_failed", receipt_id=receipt_id)
                    else:
                        print("PDF conversion succeeded; running OCR on pages")

                    page_texts: list[str] = []
                    raw_pages: list[dict] = []

                    for idx, img in enumerate(images):
                        # Ensure OCR provider only sees image bytes.
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        img_bytes = buf.getvalue()

                        page_result = await provider.extract(img_bytes, "image/png")
                        page_text = page_result.get("text") or page_result.get("ocr_text") or ""
                        if page_text and page_text.strip():
                            page_texts.append(page_text.strip())
                        raw_pages.append(page_result)
                        logger.info(
                            "receipt_pipeline_pdf_page_ocr_completed",
                            receipt_id=receipt_id,
                            page_index=idx,
                            text_length=len(page_text or ""),
                        )
                    combined_text = "\n\n".join(page_texts)
                    pages_struct = []
                    merged_lines: list[dict] = []
                    for idx, pr in enumerate(raw_pages):
                        pages_struct.append({
                            "page_index": idx,
                            "raw_text": pr.get("raw_text") or pr.get("text") or pr.get("ocr_text") or "",
                            "text": pr.get("text") or pr.get("ocr_text") or "",
                            "blocks": pr.get("blocks") or [],
                            "lines": pr.get("lines") or [],
                            "confidence_scores": pr.get("confidence_scores") or {},
                            "extraction_method": pr.get("extraction_method"),
                        })
                        if isinstance(pr.get("lines"), list):
                            for ln in pr.get("lines") or []:
                                if isinstance(ln, dict):
                                    merged_lines.append({"page_index": idx, **ln})
                    ocr_result = {
                        "text": combined_text,
                        "raw_text": combined_text,
                        "blocks": [b for p in raw_pages for b in (p.get("blocks") or [])] if raw_pages else [],
                        "lines": sorted(
                            merged_lines,
                            key=lambda l: (
                                l.get("page_index", 0),
                                (l.get("bbox") or [0, 0, 0, 0])[1],
                                (l.get("bbox") or [0, 0, 0, 0])[0],
                            ),
                        ),
                        "pages": pages_struct,
                        "raw_response": {"pages": raw_pages, "page_count": len(raw_pages)},
                        "confidence_scores": {},
                        "extraction_method": f"{getattr(settings, 'OCR_PROVIDER', '')}_pdf_combined",
                    }
                else:
                    ocr_result = await provider.extract(file_content, mime_type)

                # OCR retry if empty/too short
                txt = (ocr_result.get("text") or ocr_result.get("ocr_text") or "").strip()
                if len(txt) < 10:
                    logger.warning("receipt_pipeline_ocr_empty_retry", receipt_id=receipt_id, mime_type=mime_type)
                    try:
                        ocr_retry = await provider.extract(file_content, mime_type)
                        txt2 = (ocr_retry.get("text") or ocr_retry.get("ocr_text") or "").strip()
                        if len(txt2) > len(txt):
                            ocr_result = ocr_retry
                    except Exception as retry_err:
                        logger.warning("receipt_pipeline_ocr_retry_failed", receipt_id=receipt_id, error=str(retry_err))
                _log_pipeline_step("ocr_ok", receipt_id, extra={
                    "has_text": bool(ocr_result.get("text") or ocr_result.get("ocr_text")),
                    "text_len": len(ocr_result.get("text") or ocr_result.get("ocr_text") or ""),
                })
            except Exception as e:
                _log_pipeline_step("ocr_failed", receipt_id, error=str(e))
                if receipt and receipt.meta_data is not None:
                    _append_meta_error(receipt.meta_data, step="ocr_failed", error=str(e))
                raise

            normalized = await normalizer.normalize(ocr_result)
            ocr_text_raw = ocr_result.get("text") or ocr_result.get("ocr_text") or ""

            # Deterministic label/value alignment + merchant extraction (before regex/LLM).
            det_debug = {}
            try:
                ocr_lines = normalized.get("lines") or []
                mapped, det_debug = _deterministic_label_value_mapping(ocr_lines)
                vendor_name, vendor_debug = _deterministic_vendor_from_lines(ocr_lines)
                vendor_text_debug = {}
                if not vendor_name:
                    vendor_name_text, vendor_text_debug = _deterministic_vendor_from_text(ocr_text_raw)
                    if vendor_name_text:
                        vendor_name = vendor_name_text
                # If bbox-based vendor is missing, keep debug explainable.
                if vendor_text_debug:
                    vendor_debug = {"from_lines": vendor_debug, "from_text": vendor_text_debug}

                # Store debug for auditability (used by frontend and training exports).
                if not receipt.meta_data:
                    receipt.meta_data = {}
                receipt.meta_data.setdefault("pipeline_debug", {})
                receipt.meta_data["pipeline_debug"]["ocr_label_alignment"] = {
                    "mapped": mapped,
                    "det_debug": det_debug,
                    "vendor_debug": vendor_debug,
                }

                # Override critical fields when deterministic values exist.
                if isinstance(mapped, dict):
                    if mapped.get("subtotal") is not None:
                        normalized["subtotal"] = mapped.get("subtotal")
                    if mapped.get("vat_rate") is not None:
                        normalized["vat_rate"] = mapped.get("vat_rate")
                    if mapped.get("vat_amount") is not None:
                        normalized["vat_amount"] = mapped.get("vat_amount")
                    if mapped.get("total_amount") is not None:
                        normalized["total_amount"] = mapped.get("total_amount")

                if vendor_name:
                    normalized["merchant_name"] = vendor_name
                # If current merchant_name looks like a label (e.g. "Invoice Number"), drop it.
                mn = normalized.get("merchant_name") or ""
                mn_u = str(mn).strip().upper()
                if mn_u and re.search(r"\b(INVOICE\s*NUMBER|DATE|TOTAL(\s+DUE)?|VAT|TVA)\b", mn_u):
                    normalized["merchant_name"] = ""

                # Fallback: when bbox-based mapping didn't populate VAT/subtotal, derive from stacked text.
                if ocr_text_raw and (normalized.get("vat_amount") in (None, "", 0, 0.0)):
                    fb_amounts, fb_debug = _fallback_invoice_amounts_from_ocr_text(ocr_text_raw)
                    if fb_amounts:
                        det_debug.setdefault("text_fallback_amounts", fb_amounts)
                        det_debug.setdefault("text_fallback_debug", fb_debug)
                        # Only apply if still missing/zero.
                        if normalized.get("vat_amount") in (None, "", 0, 0.0) and fb_amounts.get("vat_amount") is not None:
                            normalized["vat_amount"] = fb_amounts.get("vat_amount")
                        if normalized.get("subtotal") in (None, "", 0, 0.0) and fb_amounts.get("subtotal") is not None:
                            normalized["subtotal"] = fb_amounts.get("subtotal")
                        if normalized.get("total_amount") in (None, "", 0, 0.0) and fb_amounts.get("total_amount") is not None:
                            normalized["total_amount"] = fb_amounts.get("total_amount")
                        if fb_amounts.get("vat_rate") is not None:
                            normalized["vat_rate"] = fb_amounts.get("vat_rate")
            except Exception as det_err:
                logger.warning("deterministic_label_alignment_failed", receipt_id=receipt_id, error=str(det_err))
                if receipt and receipt.meta_data is not None:
                    receipt.meta_data.setdefault("pipeline_debug", {})
                    receipt.meta_data["pipeline_debug"]["ocr_label_alignment_error"] = str(det_err)

            # Enrich with regex extraction (fallback when LLM not available)
            if ocr_text_raw and ocr_text_raw.strip():
                extracted = _extract_from_ocr_text(ocr_text_raw)
                for k, v in extracted.items():
                    if v is not None and (normalized.get(k) is None or normalized.get(k) == 0 or normalized.get(k) == ""):
                        normalized[k] = v

                # Re-validate merchant_name after regex fallback:
                # regex extraction can sometimes treat "Invoice Number: ..." as the merchant.
                try:
                    mn2 = normalized.get("merchant_name") or ""
                    mn2_u = str(mn2).strip().upper()
                    trap = re.search(r"\b(INVOICE\s*NUMBER|DATE|TOTAL(\s+DUE)?|VAT|TVA)\b", mn2_u) is not None
                    if trap:
                        # If we extracted a proper vendor earlier, prefer it; otherwise clear.
                        if vendor_name:
                            normalized["merchant_name"] = vendor_name
                        else:
                            normalized["merchant_name"] = ""
                except Exception:
                    pass

            # Update receipt with OCR
            receipt.ocr_status = "completed"
            if not receipt.meta_data:
                receipt.meta_data = {}
            receipt.meta_data["ocr"] = normalized

            # Pre-fill structured extraction from deterministic OCR values.
            # This ensures the frontend can render/edit fields even if the LLM step crashes
            # (e.g. missing API key or extractor regex issues).
            try:
                from services.llm_service.schemas import ReceiptExtractionResponse

                receipt.meta_data["extraction"] = ReceiptExtractionResponse(
                    receipt_id=receipt_id,
                    document_type=receipt.meta_data.get("document_type") if receipt.meta_data else None,
                    merchant_name=normalized.get("merchant_name") or None,
                    expense_date=normalized.get("expense_date") or None,
                    total_amount=normalized.get("total_amount") or None,
                    vat_amount=normalized.get("vat_amount") or None,
                    vat_rate=normalized.get("vat_rate") or None,
                    subtotal=normalized.get("subtotal") or None,
                    currency=normalized.get("currency") or "EUR",
                    line_items=[],
                    others=[],
                    confidence_scores={},
                    overall_confidence=None,
                    field_sources={},
                    field_reasoning={},
                    extraction_metadata={"provider": "ocr_pre_fill"},
                ).model_dump(mode="json")
            except Exception:
                # Best-effort; OCR values are still saved in receipt.meta_data["ocr"].
                pass

            receipt.meta_data.setdefault("pipeline", {})
            receipt.meta_data["pipeline"]["ocr_completed_at"] = datetime.utcnow().isoformat()
            attributes.flag_modified(receipt, "meta_data")
            await db.commit()
            await db.refresh(receipt)
            logger.info("ocr_saved", receipt_id=receipt_id)

            ocr_text = normalized.get("text", "") or normalized.get("ocr_text", "")
            try:
                from services.llm_service.classifier import classify_document_prd
                doc_type = classify_document_prd(ocr_text or "")
                receipt.meta_data["document_type"] = doc_type
                attributes.flag_modified(receipt, "meta_data")
                await db.commit()
            except Exception as e:
                logger.warning("document_type_classification_failed", receipt_id=receipt_id, error=str(e))
            if not (ocr_text and ocr_text.strip()):
                logger.warning("no_ocr_text", receipt_id=receipt_id)
                # Still save an empty extraction so frontend can show form for manual entry
                from services.llm_service.schemas import ReceiptExtractionResponse
                empty_extraction = ReceiptExtractionResponse(
                    receipt_id=receipt_id,
                    document_type=receipt.meta_data.get("document_type") if receipt.meta_data else None,
                    merchant_name=None,
                    expense_date=None,
                    total_amount=None,
                    currency="EUR",
                    vat_amount=None,
                    vat_rate=None,
                    confidence_scores={},
                )
                result2 = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                receipt2 = result2.scalar_one_or_none()
                if receipt2:
                    if not receipt2.meta_data:
                        receipt2.meta_data = {}
                    receipt2.meta_data["extraction"] = empty_extraction.model_dump(mode="json")
                    attributes.flag_modified(receipt2, "meta_data")
                    await db.commit()
                _log_pipeline_step("extraction_saved_empty", receipt_id)
                return

            # Step 3: LLM extraction (optional - skip if not available)
            extraction = None
            expense = None
            try:
                from services.llm_service.extractor import LLMExtractor
                from services.llm_service.schemas import ReceiptExtractionRequest
                from services.file_service.models_feedback import ReceiptExtractionCache
                from common.deterministic_extraction import extract_invoice_critical_from_pages

                # Optimization 1: reuse cached extraction by file_hash + document_type
                cached = None
                try:
                    doc_type_hint = (receipt.meta_data or {}).get("document_type") if receipt and receipt.meta_data else None
                    if receipt.file_hash and doc_type_hint:
                        r = await db.execute(
                            select(ReceiptExtractionCache).where(
                                ReceiptExtractionCache.file_hash == receipt.file_hash,
                                ReceiptExtractionCache.document_type == str(doc_type_hint),
                            )
                        )
                        cached = r.scalar_one_or_none()
                except Exception:
                    cached = None

                if cached and isinstance(cached.extraction_output, dict):
                    from services.llm_service.schemas import ReceiptExtractionResponse
                    extraction = ReceiptExtractionResponse(**{**cached.extraction_output, "receipt_id": receipt_id})
                    _log_pipeline_step("llm_skipped_cache_hit", receipt_id)
                else:
                    # Optimization 2: skip LLM if deterministic extraction covers critical fields confidently
                    skip_llm = False
                    doc_type_hint = (receipt.meta_data or {}).get("document_type") if receipt and receipt.meta_data else None
                    if doc_type_hint in ("facture_achat", "facture_vente") and isinstance(normalized.get("pages"), list) and normalized.get("pages"):
                        det = extract_invoice_critical_from_pages(normalized.get("pages"))
                        if det.total_amount is not None and det.expense_date:
                            # Deterministic has critical fields; treat as sufficient and skip LLM for cost.
                            skip_llm = True
                            fallback_ext = {
                                "receipt_id": receipt_id,
                                "document_type": doc_type_hint,
                                "merchant_name": det.merchant_name,
                                "invoice_number": None,
                                "total_amount": det.total_amount,
                                "vat_amount": det.vat_amount,
                                "vat_rate": det.vat_rate,
                                "currency": "EUR",
                                "expense_date": det.expense_date,
                                "line_items": [],
                                "others": [],
                                "confidence_scores": {
                                    "total_amount": 0.98,
                                    "expense_date": 0.98,
                                },
                                "overall_confidence": 0.98,
                                "field_sources": {
                                    "total_amount": "regex",
                                    "expense_date": "regex",
                                    "vat_amount": "regex",
                                    "vat_rate": "regex",
                                },
                                "field_reasoning": {
                                    "total_amount": "Deterministic regex (last page totals)",
                                    "expense_date": "Deterministic regex (first page date)",
                                },
                                "extraction_metadata": {"provider": "deterministic_skip_llm"},
                            }
                            fallback_ext = _apply_prd_validation(fallback_ext)
                            # Save now so UI can proceed immediately
                            receipt.meta_data["extraction"] = fallback_ext
                            attributes.flag_modified(receipt, "meta_data")
                            await db.commit()
                            _log_pipeline_step("llm_skipped_deterministic", receipt_id)

                    if not skip_llm:
                        extractor = LLMExtractor()
                        req = ReceiptExtractionRequest(
                            ocr_text=ocr_text,
                            receipt_id=receipt_id,
                            tenant_id=tenant_id,
                            language="fr",
                            document_type=receipt.meta_data.get("document_type") if receipt and receipt.meta_data else None,
                            ocr_pages=[(p.get("text") or p.get("raw_text") or "").strip() for p in (normalized.get("pages") or []) if isinstance(p, dict)],
                            ocr_lines=normalized.get("lines"),
                            ocr_blocks=normalized.get("blocks"),
                        )
                        extraction = await extractor.extract(req)
                        _log_pipeline_step("llm_ok", receipt_id, extra={"has_extraction": bool(extraction)})

                        # Save extraction cache best-effort
                        try:
                            doc_type_hint = (receipt.meta_data or {}).get("document_type") if receipt and receipt.meta_data else None
                            if receipt.file_hash and doc_type_hint and extraction:
                                ext_out = extraction.model_dump(mode="json")
                                r = await db.execute(
                                    select(ReceiptExtractionCache).where(
                                        ReceiptExtractionCache.file_hash == receipt.file_hash,
                                        ReceiptExtractionCache.document_type == str(doc_type_hint),
                                    )
                                )
                                existing = r.scalar_one_or_none()
                                if existing:
                                    existing.extraction_output = ext_out
                                else:
                                    db.add(ReceiptExtractionCache(
                                        file_hash=receipt.file_hash,
                                        document_type=str(doc_type_hint),
                                        extraction_output=ext_out,
                                    ))
                                await db.commit()
                        except Exception:
                            pass
            except Exception as e:
                _log_pipeline_step("llm_failed", receipt_id, error=str(e))
                # If any prior DB operation failed, the session may be in an aborted transaction state.
                # Roll back so we can continue writing fallback extraction safely.
                try:
                    await db.rollback()
                except Exception:
                    pass
                try:
                    if receipt and receipt.meta_data is not None:
                        _append_meta_error(receipt.meta_data, step="llm_failed", error=str(e))
                        attributes.flag_modified(receipt, "meta_data")
                        await db.commit()
                except Exception:
                    pass
                # Fallback: regex-based extraction for critical fields so frontend gets structured data.
                try:
                    raw = _extract_from_ocr_text(ocr_text)
                    fallback_ext = {
                        "receipt_id": receipt_id,
                        "document_type": receipt.meta_data.get("document_type") if receipt and receipt.meta_data else None,
                        "merchant_name": raw.get("merchant_name"),
                        "invoice_number": raw.get("invoice_number"),
                        "total_amount": raw.get("total_amount"),
                        "vat_amount": raw.get("vat_amount"),
                        "vat_rate": raw.get("vat_rate"),
                        "currency": raw.get("currency") or "EUR",
                        "expense_date": raw.get("expense_date"),
                        "line_items": [],
                        "others": [],
                        "confidence_scores": {},
                        "overall_confidence": None,
                        "extraction_metadata": {"provider": "regex_fallback"},
                    }
                    fallback_ext = _apply_prd_validation(fallback_ext)

                    # Save into receipt.meta_data.extraction and merge into ocr.
                    result_f = await db.execute(
                        select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                    )
                    receipt_f = result_f.scalar_one_or_none()
                    if receipt_f:
                        if not receipt_f.meta_data:
                            receipt_f.meta_data = {}
                        receipt_f.meta_data["extraction"] = fallback_ext
                        ocr_dict = receipt_f.meta_data.get("ocr") or {}
                        for k, v in fallback_ext.items():
                            if v is not None and k not in ("confidence_scores", "extraction_metadata"):
                                ocr_dict[k] = v
                        receipt_f.meta_data["ocr"] = ocr_dict
                        attributes.flag_modified(receipt_f, "meta_data")
                        await db.commit()
                    _log_pipeline_step("extraction_saved_regex_fallback", receipt_id)
                except Exception as fallback_err:
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                    _log_pipeline_step("regex_fallback_failed", receipt_id, error=str(fallback_err))
                # Continue without LLM - user can still fill form manually

            # Save extraction to receipt if LLM succeeded; merge into ocr so all fields available
            # Fill extraction nulls from OCR (regex fallback) - e.g. date when Gemini misses it
            if not extraction:
                # Some environments/providers may return `None` instead of raising.
                # Ensure the frontend still gets usable structured data from OCR.
                try:
                    from services.llm_service.schemas import ReceiptExtractionResponse

                    ocr_dict = (receipt.meta_data or {}).get("ocr") or {}
                    fallback_ext = ReceiptExtractionResponse(
                        receipt_id=receipt_id,
                        document_type=receipt.meta_data.get("document_type") if receipt.meta_data else None,
                        merchant_name=ocr_dict.get("merchant_name") or None,
                        expense_date=ocr_dict.get("expense_date") or None,
                        total_amount=ocr_dict.get("total_amount") or None,
                        vat_amount=ocr_dict.get("vat_amount") or None,
                        vat_rate=ocr_dict.get("vat_rate") or None,
                        subtotal=ocr_dict.get("subtotal") or None,
                        currency=ocr_dict.get("currency") or "EUR",
                        line_items=[],
                        others=[],
                        confidence_scores={},
                        overall_confidence=None,
                        field_sources={},
                        field_reasoning={},
                        extraction_metadata={"provider": "ocr_fallback_no_llm_result"},
                    )

                    has_any = any(
                        v is not None
                        for v in (
                            fallback_ext.merchant_name,
                            fallback_ext.expense_date,
                            fallback_ext.total_amount,
                            fallback_ext.vat_amount,
                            fallback_ext.subtotal,
                        )
                    )
                    if has_any and (not (receipt.meta_data or {}).get("extraction")):
                        receipt.meta_data["extraction"] = fallback_ext.model_dump(mode="json")
                        attributes.flag_modified(receipt, "meta_data")
                        await db.commit()
                except Exception as fb_err:
                    logger.warning(
                        "ocr_fallback_extraction_failed",
                        receipt_id=receipt_id,
                        error=str(fb_err),
                    )

            if extraction:
                result2 = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                receipt2 = result2.scalar_one_or_none()
                if receipt2:
                    if not receipt2.meta_data:
                        receipt2.meta_data = {}
                    ocr_dict = receipt2.meta_data.get("ocr") or {}
                    ext_dict = extraction.model_dump(mode="json")
                    if not ext_dict.get("document_type") and receipt2.meta_data.get("document_type"):
                        ext_dict["document_type"] = receipt2.meta_data.get("document_type")
                    # Fill null/zero extraction fields from OCR (deterministic/regex)
                    for field in ("expense_date", "merchant_name", "total_amount", "vat_amount", "vat_rate", "subtotal"):
                        ext_val = ext_dict.get(field)
                        ocr_val = ocr_dict.get(field)
                        fill_from_ocr = ocr_val is not None and (
                            ext_val is None or
                            (field in ("total_amount", "vat_amount") and ext_val == 0)
                        )
                        if fill_from_ocr:
                            ext_dict[field] = ocr_val

                    # Deterministic enforcement: prevent LLM from overwriting critical label-aligned values.
                    # If OCR deterministic values exist and differ from LLM extraction, keep OCR values and flag mismatch.
                    try:
                        mismatch_fields = []
                        tol = 0.02
                        def _num_diff(a, b) -> bool:
                            try:
                                return abs(float(a) - float(b)) > tol
                            except Exception:
                                return False

                        def _is_missing_or_zero(v) -> bool:
                            if v is None:
                                return True
                            if v == "":
                                return True
                            try:
                                return float(v) == 0.0
                            except Exception:
                                return False

                        for field in ("total_amount", "vat_amount", "subtotal", "vat_rate"):
                            ocr_val = ocr_dict.get(field)
                            llm_val = ext_dict.get(field)
                            if _is_missing_or_zero(ocr_val) or _is_missing_or_zero(llm_val):
                                continue
                            if _num_diff(ocr_val, llm_val):
                                mismatch_fields.append(field)
                                ext_dict[field] = ocr_val

                        # Merchant must be vendor entity (avoid "Invoice Number"/labels as merchant).
                        mn_ocr = (ocr_dict.get("merchant_name") or "").strip()
                        mn_llm = (ext_dict.get("merchant_name") or "").strip()
                        if mn_llm:
                            mn_llm_u = mn_llm.upper()
                            if re.search(r"\b(INVOICE\s*NUMBER|DATE|TOTAL(\s+DUE)?|VAT|TVA)\b", mn_llm_u):
                                mismatch_fields.append("merchant_name")
                                ext_dict["merchant_name"] = mn_ocr
                        if mn_ocr and mn_llm and mn_ocr != mn_llm:
                            mismatch_fields.append("merchant_name")
                            ext_dict["merchant_name"] = mn_ocr

                        if mismatch_fields:
                            ext_dict.setdefault("validation_flags", [])
                            if "incorrect_mapping" not in ext_dict["validation_flags"]:
                                ext_dict["validation_flags"].append("incorrect_mapping")
                            ext_dict["status"] = (
                                "needs_review"
                                if ext_dict.get("status") != "REQUIRES_MANUAL_VALIDATION"
                                else ext_dict.get("status")
                            )

                        # Deterministic financial consistency validation:
                        # For invoices, expect: subtotal + vat_amount ≈ total_amount (gross).
                        try:
                            def _to_float(v):
                                if v is None:
                                    return None
                                try:
                                    return float(v)
                                except Exception:
                                    return None

                            subtotal_v = _to_float(ext_dict.get("subtotal"))
                            vat_v = _to_float(ext_dict.get("vat_amount"))
                            total_v = _to_float(ext_dict.get("total_amount"))
                            if subtotal_v is not None and vat_v is not None and total_v is not None:
                                if abs((subtotal_v + vat_v) - total_v) > 0.05:
                                    ext_dict.setdefault("validation_flags", [])
                                    if "incorrect_mapping" not in ext_dict["validation_flags"]:
                                        ext_dict["validation_flags"].append("incorrect_mapping")
                                    ext_dict["status"] = (
                                        "needs_review"
                                        if ext_dict.get("status") != "REQUIRES_MANUAL_VALIDATION"
                                        else ext_dict.get("status")
                                    )
                        except Exception:
                            pass
                    except Exception as enf_err:
                        logger.warning("deterministic_enforcement_failed", receipt_id=receipt_id, error=str(enf_err))

                    # Debug logging for Gemini mapping quality
                    try:
                        if isinstance(ext_dict.get("extraction_metadata"), dict):
                            llm_debug = ext_dict["extraction_metadata"].get("llm_debug")
                            if llm_debug:
                                receipt2.meta_data.setdefault("pipeline_debug", {})
                                receipt2.meta_data["pipeline_debug"]["llm_debug"] = llm_debug
                        receipt2.meta_data.setdefault("pipeline_debug", {})
                        receipt2.meta_data["pipeline_debug"]["final_mapped_values"] = {
                            "merchant_name": ext_dict.get("merchant_name"),
                            "subtotal": ext_dict.get("subtotal"),
                            "vat_amount": ext_dict.get("vat_amount"),
                            "total_amount": ext_dict.get("total_amount"),
                            "vat_rate": ext_dict.get("vat_rate"),
                            "status": ext_dict.get("status"),
                            "validation_flags": ext_dict.get("validation_flags", []),
                        }
                    except Exception:
                        pass

                    # Enhance confidence/auditability using OCR evidence, then apply PRD validation/status.
                    ocr_text_for_evidence = (ocr_dict.get("raw_text") or ocr_dict.get("text") or "") if isinstance(ocr_dict, dict) else ""
                    ocr_overall = None
                    if isinstance(ocr_dict, dict):
                        cs = ocr_dict.get("confidence_scores") or {}
                        if isinstance(cs, dict):
                            ocr_overall = cs.get("overall")
                    ext_dict = _enhance_confidence_and_audit(ext_dict, ocr_text=ocr_text_for_evidence, ocr_confidence=ocr_overall)

                    # Deterministic extraction + cross-check for invoices (flag inconsistencies)
                    try:
                        from common.deterministic_extraction import extract_invoice_critical_from_pages, cross_check_invoice_llm
                        doc_type = ext_dict.get("document_type")
                        if doc_type in ("facture_achat", "facture_vente"):
                            pages = []
                            if isinstance(ocr_dict, dict) and isinstance(ocr_dict.get("pages"), list):
                                pages = ocr_dict.get("pages")
                            det = extract_invoice_critical_from_pages(pages)
                            # Fill missing criticals from deterministic layer
                            if ext_dict.get("total_amount") in (None, "", 0) and det.total_amount is not None:
                                ext_dict["total_amount"] = det.total_amount
                                ext_dict.setdefault("field_sources", {})["total_amount"] = "regex"
                            if ext_dict.get("vat_amount") in (None, "", 0) and det.vat_amount is not None:
                                ext_dict["vat_amount"] = det.vat_amount
                                ext_dict.setdefault("field_sources", {})["vat_amount"] = "regex"
                            if ext_dict.get("vat_rate") in (None, "", 0) and det.vat_rate is not None:
                                ext_dict["vat_rate"] = det.vat_rate
                                ext_dict.setdefault("field_sources", {})["vat_rate"] = "regex"
                            if ext_dict.get("expense_date") in (None, "") and det.expense_date:
                                ext_dict["expense_date"] = det.expense_date
                                ext_dict.setdefault("field_sources", {})["expense_date"] = "regex"

                            flags, reasons = cross_check_invoice_llm(deterministic=det, llm=ext_dict)
                            if flags:
                                ext_dict.setdefault("validation_flags", [])
                                ext_dict["validation_flags"].extend([f for f in flags if f not in ext_dict["validation_flags"]])
                                ext_dict.setdefault("field_reasoning", {}).update(reasons)
                                if ext_dict.get("status") is None or ext_dict.get("status") == "completed":
                                    ext_dict["status"] = "needs_review"
                    except Exception as det_err:
                        logger.warning("deterministic_cross_check_failed", receipt_id=receipt_id, error=str(det_err))

                    ext_dict = _apply_prd_validation(ext_dict)
                    receipt2.meta_data["extraction"] = ext_dict
                    # Merge extraction into ocr so consumers reading only ocr get all fields
                    for k, v in ext_dict.items():
                        if v is not None and k not in ("confidence_scores", "extraction_metadata"):
                            ocr_dict[k] = v
                    receipt2.meta_data["ocr"] = ocr_dict
                    attributes.flag_modified(receipt2, "meta_data")
                    await db.commit()
                logger.info("extraction_saved", receipt_id=receipt_id)

            # Finalize pipeline timing + stage status
            try:
                result_f = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                receipt_f = result_f.scalar_one_or_none()
                if receipt_f:
                    if not receipt_f.meta_data:
                        receipt_f.meta_data = {}
                    receipt_f.meta_data.setdefault("pipeline", {})
                    receipt_f.meta_data["pipeline"]["completed_at"] = datetime.utcnow().isoformat()
                    receipt_f.meta_data["pipeline"]["duration_ms"] = int((time.time() - started) * 1000)
                    attributes.flag_modified(receipt_f, "meta_data")
                    await db.commit()
            except Exception:
                pass

            # Use merged data for expense creation (extraction + OCR fallback)
            merged_date = extraction.expense_date if extraction else None
            merged_amount = extraction.total_amount if extraction else None
            if extraction and receipt2 and receipt2.meta_data:
                ext = receipt2.meta_data.get("extraction") or {}
                if merged_date is None and ext.get("expense_date"):
                    try:
                        merged_date = datetime.strptime(str(ext["expense_date"]), "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        pass
                if merged_amount is None and ext.get("total_amount") is not None:
                    try:
                        merged_amount = Decimal(str(ext["total_amount"]))
                    except (ValueError, TypeError):
                        pass

            if extraction and merged_amount and merged_date:
                expense = Expense(
                    tenant_id=uuid_lib.UUID(tenant_id),
                    submitted_by=uuid_lib.UUID(user_id),
                    amount=merged_amount,
                    currency=extraction.currency or "EUR",
                    expense_date=merged_date,
                    category=None,
                    description=extraction.description or f"Receipt from {extraction.merchant_name or 'Unknown'}",
                    merchant_name=extraction.merchant_name,
                    vat_amount=extraction.vat_amount,
                    vat_rate=float(extraction.vat_rate) if extraction.vat_rate is not None else None,
                    status="draft",
                    meta_data={
                        "receipt_id": receipt_id,
                        "auto_created": True,
                        "extraction_confidence": extraction.confidence_scores,
                    },
                )
                db.add(expense)
                await db.flush()
                # Link receipt to the auto-created expense
                result_receipt = await db.execute(
                    select(ReceiptDocument).where(
                        ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                        ReceiptDocument.deleted_at.is_(None),
                    )
                )
                rec = result_receipt.scalar_one_or_none()
                if rec:
                    rec.expense_id = expense.id
                    logger.info("receipt_linked_to_expense", receipt_id=receipt_id, expense_id=str(expense.id))
                    await db.commit()
                else:
                    await db.commit()
                logger.info("expense_created", receipt_id=receipt_id, expense_id=str(expense.id))

            # Step 4: Embed receipt into RAG document store so audit QA can retrieve it
            try:
                from services.rag_service.embeddings import EmbeddingsPipeline

                # Re-fetch latest receipt (to get file_name, meta_data)
                result3 = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                rec_for_embed = result3.scalar_one_or_none() or receipt

                ocr_dict = {}
                if rec_for_embed and rec_for_embed.meta_data:
                    ocr_dict = rec_for_embed.meta_data.get("ocr") or {}

                # Build a human-readable content block mixing extraction summary and OCR text
                ocr_text_for_embed = ocr_dict.get("text") or ocr_dict.get("ocr_text") or ocr_text
                title_parts = ["Receipt"]
                if extraction and extraction.merchant_name:
                    title_parts.append(extraction.merchant_name)
                if merged_date:
                    title_parts.append(str(merged_date))
                title = " - ".join(title_parts)

                file_name = getattr(rec_for_embed, "file_name", None) or file_metadata.get("file_name") or "receipt"
                content_lines = [
                    f"Receipt ID: {receipt_id}",
                    f"File name: {file_name}",
                    f"Tenant ID: {tenant_id}",
                ]
                if extraction:
                    content_lines.extend(
                        [
                            f"Merchant: {extraction.merchant_name or 'Unknown'}",
                            f"Date: {merged_date}" if merged_date else "",
                            f"Total amount: {merged_amount} {extraction.currency or 'EUR'}" if merged_amount else "",
                            f"VAT amount: {extraction.vat_amount} at {extraction.vat_rate}%" if extraction.vat_amount is not None else "",
                            f"Description: {extraction.description}" if extraction.description else "",
                        ]
                    )
                content_lines.append("")
                content_lines.append("OCR Text:")
                content_lines.append(ocr_text_for_embed or "")

                content = "\n".join([line for line in content_lines if line is not None])

                metadata = {
                    "receipt_id": receipt_id,
                    "tenant_id": tenant_id,
                    "file_id": str(getattr(rec_for_embed, "file_id", "")) if rec_for_embed else None,
                    "expense_id": str(expense.id) if expense else None,
                    "merchant_name": extraction.merchant_name if extraction else None,
                    "expense_date": str(merged_date) if merged_date else None,
                    "total_amount": float(merged_amount) if merged_amount else None,
                }

                pipeline = EmbeddingsPipeline(db, tenant_id)
                await pipeline.embed_document(
                    document_type="receipt",
                    document_id=receipt_id,
                    title=title,
                    content=content,
                    created_by=user_id,
                    metadata=metadata,
                )
                _log_pipeline_step(
                    "rag_receipt_embedded",
                    receipt_id,
                    extra={"has_extraction": bool(extraction), "has_ocr_text": bool(ocr_text_for_embed)},
                )
            except Exception as e:
                # Never fail the receipt pipeline because RAG embedding failed
                logger.error("embed_receipt_rag_failed", receipt_id=receipt_id, error=str(e))
        _log_pipeline_step("done", receipt_id)
    except Exception as e:
        _log_pipeline_step("pipeline_failed", receipt_id, error=str(e))
        logger.error("receipt_pipeline_failed", receipt_id=receipt_id, error=str(e), exc_info=True)
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                r = result.scalar_one_or_none()
                if r:
                    r.ocr_status = "failed"
                    if not r.meta_data:
                        r.meta_data = {}
                    r.meta_data["pipeline_error"] = str(e)
                    attributes.flag_modified(r, "meta_data")
                    await db.commit()
        except Exception:
            pass
