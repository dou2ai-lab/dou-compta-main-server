"""
COMPTAA Agent - Automatic Journal Entry Generator.
Generates PCG 2025-compliant double-entry journal entries from expenses.
"""
import structlog
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from common.agent_base import AgentBase, AgentResult, AgentStatus
from .models import JournalEntry, JournalEntryLine, FiscalPeriod, ThirdParty
from .config import VAT_RATES, JOURNAL_CODES

logger = structlog.get_logger()

# Category to PCG account mapping (expense categories -> PCG 6xxxx accounts)
CATEGORY_ACCOUNT_MAP = {
    # Travel & Transport
    "transport": "625100",
    "voyage": "625100",
    "travel": "625100",
    "deplacement": "625100",
    "taxi": "625100",
    "train": "625100",
    "avion": "625100",
    # Meals & Entertainment
    "repas": "625700",
    "restaurant": "625700",
    "meal": "625700",
    "meals": "625700",
    "reception": "625700",
    # Accommodation
    "hotel": "625600",
    "hebergement": "625600",
    "accommodation": "625600",
    "mission": "625600",
    # Office Supplies
    "fournitures": "606400",
    "supplies": "606400",
    "office": "606400",
    "papeterie": "606400",
    # Telecom
    "telephone": "626000",
    "telecom": "626000",
    "internet": "626000",
    # Professional Services
    "honoraires": "622600",
    "consulting": "622600",
    "conseil": "622600",
    # Insurance
    "assurance": "616000",
    "insurance": "616000",
    # Rent
    "loyer": "613200",
    "rent": "613200",
    # IT Equipment
    "informatique": "218300",
    "materiel": "218300",
    "equipment": "218300",
    # Gifts
    "cadeau": "623400",
    "gift": "623400",
    # Subscriptions
    "abonnement": "613500",
    "subscription": "613500",
    # General purchases
    "achat": "607000",
    "purchase": "607000",
    # Default
    "autres": "628000",
    "other": "628000",
}

# Default supplier account
DEFAULT_SUPPLIER_ACCOUNT = "401100"
# TVA deductible sur ABS
TVA_DEDUCTIBLE_ACCOUNT = "445660"


def resolve_expense_account(category: str, gl_account_code: Optional[str] = None) -> str:
    """Resolve the PCG expense account from category or GL mapping."""
    if gl_account_code:
        return gl_account_code

    if category:
        cat_lower = category.lower().strip()
        for key, code in CATEGORY_ACCOUNT_MAP.items():
            if key in cat_lower:
                return code

    return "628000"  # Divers - default


def compute_vat_decomposition(total_ttc: Decimal, vat_rate: Decimal) -> tuple[Decimal, Decimal]:
    """Decompose TTC amount into HT + VAT amounts.

    total_ttc = total_ht * (1 + vat_rate/100)
    total_ht = total_ttc / (1 + vat_rate/100)
    vat_amount = total_ttc - total_ht
    """
    if not vat_rate or vat_rate == 0:
        return total_ttc, Decimal("0")

    rate_factor = Decimal("1") + (vat_rate / Decimal("100"))
    total_ht = (total_ttc / rate_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat_amount = (total_ttc - total_ht).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return total_ht, vat_amount


async def generate_entry_number(db: AsyncSession, tenant_id: UUID, journal_code: str) -> str:
    """Generate next sequential entry number for a journal."""
    result = await db.execute(
        select(func.count(JournalEntry.id)).where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntry.journal_code == journal_code,
        )
    )
    count = result.scalar() or 0
    return f"{journal_code}-{count + 1:06d}"


async def determine_fiscal_period(db: AsyncSession, tenant_id: UUID, entry_date: date) -> tuple[int, int]:
    """Find fiscal year and period for a given date."""
    result = await db.execute(
        select(FiscalPeriod).where(
            FiscalPeriod.tenant_id == tenant_id,
            FiscalPeriod.start_date <= entry_date,
            FiscalPeriod.end_date >= entry_date,
            FiscalPeriod.status == "open",
        )
    )
    period = result.scalar_one_or_none()

    if period:
        return period.fiscal_year, period.period_number

    # Fallback: derive from date (calendar year = fiscal year, month = period)
    return entry_date.year, entry_date.month


async def generate_expense_entry(
    db: AsyncSession,
    tenant_id: UUID,
    expense_id: UUID,
    amount: Decimal,
    category: str,
    description: str,
    expense_date: date,
    vat_rate: Optional[Decimal] = None,
    vat_amount: Optional[Decimal] = None,
    merchant_name: Optional[str] = None,
    gl_account_code: Optional[str] = None,
    created_by: Optional[UUID] = None,
) -> JournalEntry:
    """
    Generate a complete journal entry from an approved expense.

    Standard expense entry (purchase journal ACH):
      Debit: 6xxxxx (expense account)    = HT amount
      Debit: 445660 (TVA deductible)     = VAT amount (if applicable)
      Credit: 401xxx (supplier account)  = TTC amount
    """
    journal_code = "ACH"

    # Resolve accounts
    expense_account = resolve_expense_account(category, gl_account_code)
    supplier_account = DEFAULT_SUPPLIER_ACCOUNT

    # Compute VAT decomposition
    if vat_rate and vat_rate > 0:
        if vat_amount and vat_amount > 0:
            # Use provided VAT amount, derive HT
            ht_amount = amount - vat_amount
        else:
            # Compute from rate (amount is TTC)
            ht_amount, vat_amount = compute_vat_decomposition(amount, vat_rate)
    else:
        ht_amount = amount
        vat_amount = Decimal("0")
        vat_rate = Decimal("0")

    # Generate entry number and determine fiscal period
    entry_number = await generate_entry_number(db, tenant_id, journal_code)
    fiscal_year, fiscal_period = await determine_fiscal_period(db, tenant_id, expense_date)

    # Build label
    label = description or f"Achat {category or ''}"
    if merchant_name:
        label = f"{merchant_name} - {label}"

    # Create journal entry
    entry = JournalEntry(
        id=uuid4(),
        tenant_id=tenant_id,
        entry_number=entry_number,
        journal_code=journal_code,
        entry_date=expense_date,
        description=label,
        status="draft",
        source_type="expense",
        source_id=expense_id,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        total_debit=amount,
        total_credit=amount,
        is_balanced=True,
        created_by=created_by,
    )

    # Line 1: Debit expense account (HT)
    line_num = 1
    lines = []

    lines.append(JournalEntryLine(
        id=uuid4(),
        entry_id=entry.id,
        line_number=line_num,
        account_code=expense_account,
        account_name=f"Charge {category or 'diverse'}",
        debit=ht_amount,
        credit=Decimal("0"),
        label=label,
    ))
    line_num += 1

    # Line 2: Debit TVA deductible (if VAT > 0)
    if vat_amount and vat_amount > 0:
        lines.append(JournalEntryLine(
            id=uuid4(),
            entry_id=entry.id,
            line_number=line_num,
            account_code=TVA_DEDUCTIBLE_ACCOUNT,
            account_name="TVA deductible sur ABS",
            debit=vat_amount,
            credit=Decimal("0"),
            label=f"TVA {vat_rate}%",
            vat_rate=vat_rate,
            vat_amount=vat_amount,
        ))
        line_num += 1

    # Line 3: Credit supplier account (TTC)
    lines.append(JournalEntryLine(
        id=uuid4(),
        entry_id=entry.id,
        line_number=line_num,
        account_code=supplier_account,
        account_name="Fournisseurs",
        debit=Decimal("0"),
        credit=amount,
        label=label,
    ))

    entry.lines = lines
    db.add(entry)
    await db.flush()

    logger.info(
        "journal_entry_generated",
        entry_number=entry_number,
        expense_id=str(expense_id),
        amount=str(amount),
        vat_rate=str(vat_rate),
        lines=len(lines),
    )

    return entry


class COMPTAAAgent(AgentBase):
    """COMPTAA - Automatic Accounting Agent."""

    agent_code = "COMPTAA"
    agent_name = "Agent Comptable Automatique"

    async def run(self, context: dict, result: AgentResult) -> dict:
        db = context["db"]
        tenant_id = context["tenant_id"]
        expense = context["expense"]

        result.add_log(f"Generating entry for expense {expense['id']}")

        entry = await generate_expense_entry(
            db=db,
            tenant_id=tenant_id,
            expense_id=expense["id"],
            amount=Decimal(str(expense["amount"])),
            category=expense.get("category", ""),
            description=expense.get("description", ""),
            expense_date=expense["expense_date"] if isinstance(expense["expense_date"], date) else date.fromisoformat(str(expense["expense_date"])),
            vat_rate=Decimal(str(expense["vat_rate"])) if expense.get("vat_rate") else None,
            vat_amount=Decimal(str(expense["vat_amount"])) if expense.get("vat_amount") else None,
            merchant_name=expense.get("merchant_name"),
            gl_account_code=expense.get("gl_account_code"),
            created_by=context.get("user_id"),
        )

        result.confidence = 0.95
        return {
            "entry_id": str(entry.id),
            "entry_number": entry.entry_number,
            "total_debit": str(entry.total_debit),
            "total_credit": str(entry.total_credit),
            "lines_count": len(entry.lines),
        }

    async def validate(self, result: AgentResult) -> bool:
        if result.status != AgentStatus.SUCCESS:
            return False
        data = result.data
        if not data:
            return False
        return data.get("total_debit") == data.get("total_credit")
