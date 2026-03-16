"""
Bank Statement Parser.
Parses CSV, CAMT.053 XML, and OFX bank statement formats.
"""
import csv
import io
import xml.etree.ElementTree as ET
import structlog
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from .models import BankTransaction, BankStatement

logger = structlog.get_logger()


def parse_csv_statement(
    content: str,
    bank_account_id: UUID,
    statement_id: Optional[UUID] = None,
) -> list[dict]:
    """
    Parse a CSV bank statement.
    Expected columns: date, label, amount (or debit/credit), reference, counterparty
    Flexible: tries multiple common French bank CSV formats.
    """
    transactions = []
    reader = csv.DictReader(io.StringIO(content), delimiter=';')

    # Normalize headers
    if reader.fieldnames:
        normalized = {h.strip().lower(): h for h in reader.fieldnames}
    else:
        return transactions

    for row in reader:
        # Normalize row keys
        norm_row = {k.strip().lower(): v.strip() if v else '' for k, v in row.items()}

        # Parse date
        txn_date = None
        for date_key in ['date', 'date operation', 'date_operation', 'date comptable']:
            val = norm_row.get(date_key, '')
            if val:
                txn_date = _parse_french_date(val)
                if txn_date:
                    break

        if not txn_date:
            continue

        # Parse amount
        amount = Decimal("0")
        for amt_key in ['montant', 'amount', 'montant eur']:
            val = norm_row.get(amt_key, '')
            if val:
                amount = _parse_french_amount(val)
                break
        else:
            # Try debit/credit columns
            debit = _parse_french_amount(norm_row.get('debit', '') or norm_row.get('débit', ''))
            credit = _parse_french_amount(norm_row.get('credit', '') or norm_row.get('crédit', ''))
            if debit:
                amount = -abs(debit)
            elif credit:
                amount = abs(credit)

        if amount == 0:
            continue

        label = norm_row.get('libelle', '') or norm_row.get('label', '') or norm_row.get('libellé', '') or ''
        reference = norm_row.get('reference', '') or norm_row.get('ref', '') or ''
        counterparty = norm_row.get('contrepartie', '') or norm_row.get('counterparty', '') or ''

        transactions.append({
            "bank_account_id": bank_account_id,
            "statement_id": statement_id,
            "transaction_date": txn_date,
            "amount": amount,
            "label": label,
            "reference": reference or None,
            "counterparty_name": counterparty or None,
            "transaction_type": "credit" if amount > 0 else "debit",
        })

    logger.info("csv_parsed", count=len(transactions))
    return transactions


def parse_camt053(
    xml_content: str,
    bank_account_id: UUID,
    statement_id: Optional[UUID] = None,
) -> tuple[dict, list[dict]]:
    """
    Parse CAMT.053 XML bank statement (ISO 20022).
    Returns (statement_info, transactions).
    """
    ns = {'camt': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.02'}

    # Try without namespace if not found
    root = ET.fromstring(xml_content)
    stmt_elem = root.find('.//camt:Stmt', ns)
    if stmt_elem is None:
        # Try common alternative namespaces
        for alt_ns in ['urn:iso:std:iso:20022:tech:xsd:camt.053.001.08', '']:
            ns2 = {'camt': alt_ns} if alt_ns else {}
            prefix = 'camt:' if alt_ns else ''
            stmt_elem = root.find(f'.//{prefix}Stmt', ns2 if alt_ns else None)
            if stmt_elem is not None:
                ns = ns2
                break

    statement_info = {}
    transactions = []

    if stmt_elem is None:
        logger.warning("camt053_no_statement_found")
        return statement_info, transactions

    # Extract statement info
    prefix = 'camt:' if ns.get('camt') else ''

    bal_elems = stmt_elem.findall(f'{prefix}Bal', ns) if ns.get('camt') else stmt_elem.findall('Bal')
    for bal in bal_elems:
        tp = bal.findtext(f'{prefix}Tp/{prefix}CdOrPrtry/{prefix}Cd', '', ns) if ns.get('camt') else bal.findtext('Tp/CdOrPrtry/Cd', '')
        amt_elem = bal.find(f'{prefix}Amt', ns) if ns.get('camt') else bal.find('Amt')
        if amt_elem is not None:
            amt = Decimal(amt_elem.text or '0')
            if tp == 'OPBD':
                statement_info['opening_balance'] = amt
            elif tp == 'CLBD':
                statement_info['closing_balance'] = amt

    # Extract entries
    entry_tag = f'{prefix}Ntry' if ns.get('camt') else 'Ntry'
    entries = stmt_elem.findall(entry_tag, ns) if ns.get('camt') else stmt_elem.findall(entry_tag)

    for entry in entries:
        get = lambda tag: entry.findtext(f'{prefix}{tag}', '', ns) if ns.get('camt') else entry.findtext(tag, '')

        amt_elem = entry.find(f'{prefix}Amt', ns) if ns.get('camt') else entry.find('Amt')
        amount = Decimal(amt_elem.text or '0') if amt_elem is not None else Decimal('0')

        cdt_dbt = get('CdtDbtInd')
        if cdt_dbt == 'DBIT':
            amount = -abs(amount)

        booking_date = get('BookgDt/Dt') or get('BookgDt/DtTm')
        value_date = get('ValDt/Dt') or get('ValDt/DtTm')

        txn_date = _parse_iso_date(booking_date)
        val_date = _parse_iso_date(value_date)

        label = get('AddtlNtryInf') or get('NtryDtls/TxDtls/RmtInf/Ustrd') or ''
        ref = get('NtryRef') or get('AcctSvcrRef') or ''

        transactions.append({
            "bank_account_id": bank_account_id,
            "statement_id": statement_id,
            "transaction_date": txn_date or date.today(),
            "value_date": val_date,
            "amount": amount,
            "label": label,
            "reference": ref or None,
            "transaction_type": "credit" if amount > 0 else "debit",
        })

    logger.info("camt053_parsed", entries=len(transactions))
    return statement_info, transactions


def _parse_french_date(s: str) -> Optional[date]:
    """Parse French date formats: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD."""
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y'):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_iso_date(s: str) -> Optional[date]:
    """Parse ISO date (YYYY-MM-DD or datetime)."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).date()
    except (ValueError, TypeError):
        return _parse_french_date(s)


def _parse_french_amount(s: str) -> Decimal:
    """Parse French-format amount: 1 234,56 or -1234.56."""
    if not s or not s.strip():
        return Decimal("0")
    s = s.strip().replace(' ', '').replace('\xa0', '')
    s = s.replace(',', '.')
    try:
        return Decimal(s)
    except Exception:
        return Decimal("0")
