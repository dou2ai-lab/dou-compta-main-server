"""
Banking Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import BankingService
from .reconciliation_engine import reconcile_all
from .statement_parser import parse_csv_statement, parse_camt053
from .schemas import (
    BankAccountCreate, BankAccountUpdate, BankAccountResponse, BankAccountListResponse,
    BankTransactionResponse, BankTransactionListResponse,
    BankStatementResponse, ManualTransactionCreate,
    MatchTransactionRequest, ReconciliationRuleCreate, ReconciliationRuleResponse,
    ReconciliationSummary,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Bank Accounts ---

@router.get("/accounts", response_model=BankAccountListResponse)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    accounts = await svc.list_accounts(current_user.tenant_id)
    return BankAccountListResponse(
        data=[BankAccountResponse(
            id=a.id, account_name=a.account_name, iban=a.iban, bic=a.bic,
            bank_name=a.bank_name, currency=a.currency, balance=a.balance,
            balance_date=a.balance_date, pcg_account_code=a.pcg_account_code,
            connection_type=a.connection_type, is_active=a.is_active,
            last_sync_at=a.last_sync_at, created_at=a.created_at,
        ) for a in accounts],
        total=len(accounts),
    )


@router.post("/accounts", response_model=BankAccountResponse)
async def create_account(
    payload: BankAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    account = await svc.create_account(
        current_user.tenant_id, **payload.model_dump()
    )
    await db.commit()
    return BankAccountResponse(
        id=account.id, account_name=account.account_name, iban=account.iban,
        bic=account.bic, bank_name=account.bank_name, currency=account.currency,
        balance=account.balance, balance_date=account.balance_date,
        pcg_account_code=account.pcg_account_code, connection_type=account.connection_type,
        is_active=account.is_active, last_sync_at=account.last_sync_at,
        created_at=account.created_at,
    )


@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    account = await svc.get_account(current_user.tenant_id, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouve")
    return BankAccountResponse(
        id=account.id, account_name=account.account_name, iban=account.iban,
        bic=account.bic, bank_name=account.bank_name, currency=account.currency,
        balance=account.balance, balance_date=account.balance_date,
        pcg_account_code=account.pcg_account_code, connection_type=account.connection_type,
        is_active=account.is_active, last_sync_at=account.last_sync_at,
        created_at=account.created_at,
    )


@router.put("/accounts/{account_id}", response_model=BankAccountResponse)
async def update_account(
    account_id: UUID,
    payload: BankAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    account = await svc.update_account(
        current_user.tenant_id, account_id,
        **payload.model_dump(exclude_none=True),
    )
    if not account:
        raise HTTPException(status_code=404, detail="Compte bancaire non trouve")
    await db.commit()
    return BankAccountResponse(
        id=account.id, account_name=account.account_name, iban=account.iban,
        bic=account.bic, bank_name=account.bank_name, currency=account.currency,
        balance=account.balance, balance_date=account.balance_date,
        pcg_account_code=account.pcg_account_code, connection_type=account.connection_type,
        is_active=account.is_active, last_sync_at=account.last_sync_at,
        created_at=account.created_at,
    )


# --- Transactions ---

@router.get("/accounts/{account_id}/transactions", response_model=BankTransactionListResponse)
async def list_transactions(
    account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    txns, total = await svc.list_transactions(
        account_id, page, page_size, status, start_date, end_date,
    )
    return BankTransactionListResponse(
        data=[BankTransactionResponse(
            id=t.id, bank_account_id=t.bank_account_id,
            transaction_date=t.transaction_date, value_date=t.value_date,
            amount=t.amount, currency=t.currency, label=t.label,
            reference=t.reference, counterparty_name=t.counterparty_name,
            transaction_type=t.transaction_type, category=t.category,
            reconciliation_status=t.reconciliation_status,
            matched_entry_id=t.matched_entry_id,
            match_confidence=t.match_confidence,
            matched_at=t.matched_at, matched_by=t.matched_by,
            created_at=t.created_at,
        ) for t in txns],
        total=total, page=page, page_size=page_size,
    )


@router.post("/accounts/{account_id}/transactions", response_model=BankTransactionResponse)
async def create_manual_transaction(
    account_id: UUID,
    payload: ManualTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    txn = await svc.create_transaction(
        bank_account_id=account_id,
        **payload.model_dump(),
    )
    await db.commit()
    return BankTransactionResponse(
        id=txn.id, bank_account_id=txn.bank_account_id,
        transaction_date=txn.transaction_date, value_date=txn.value_date,
        amount=txn.amount, currency=txn.currency, label=txn.label,
        reference=txn.reference, counterparty_name=txn.counterparty_name,
        transaction_type=txn.transaction_type, category=txn.category,
        reconciliation_status=txn.reconciliation_status,
        matched_entry_id=txn.matched_entry_id,
        match_confidence=txn.match_confidence,
        matched_at=txn.matched_at, matched_by=txn.matched_by,
        created_at=txn.created_at,
    )


# --- Match/Unmatch ---

@router.post("/transactions/{transaction_id}/match")
async def match_transaction(
    transaction_id: UUID,
    payload: MatchTransactionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    txn = await svc.match_transaction(transaction_id, payload.entry_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction non trouvee")
    await db.commit()
    return {"success": True, "transaction_id": str(txn.id)}


@router.post("/transactions/{transaction_id}/unmatch")
async def unmatch_transaction(
    transaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    txn = await svc.unmatch_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction non trouvee")
    await db.commit()
    return {"success": True}


# --- Statement Upload ---

@router.post("/accounts/{account_id}/upload-statement")
async def upload_statement(
    account_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload and parse a bank statement (CSV or CAMT.053 XML)."""
    svc = BankingService(db)
    content = (await file.read()).decode("utf-8", errors="replace")
    filename = file.filename or ""

    # Create statement record
    stmt = await svc.create_statement(
        bank_account_id=account_id,
        statement_date=date.today(),
        file_format="camt053" if filename.endswith(".xml") else "csv",
        imported_by=current_user.id,
    )

    # Parse
    transactions = []
    try:
        if filename.endswith(".xml"):
            stmt_info, transactions = parse_camt053(content, account_id, stmt.id)
            if stmt_info.get("opening_balance"):
                stmt.opening_balance = stmt_info["opening_balance"]
            if stmt_info.get("closing_balance"):
                stmt.closing_balance = stmt_info["closing_balance"]
        else:
            transactions = parse_csv_statement(content, account_id, stmt.id)

        # Insert transactions
        for txn_data in transactions:
            await svc.create_transaction(**txn_data)

        stmt.transaction_count = len(transactions)
        stmt.import_status = "completed"
    except Exception as e:
        logger.error("statement_parse_failed", error=str(e))
        stmt.import_status = "failed"
        stmt.error_message = str(e)

    await db.commit()
    return {
        "statement_id": str(stmt.id),
        "transactions_imported": len(transactions),
        "status": stmt.import_status,
    }


# --- Reconciliation ---

@router.post("/accounts/{account_id}/reconcile", response_model=dict)
async def run_reconciliation(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run automatic reconciliation for a bank account."""
    stats = await reconcile_all(db, current_user.tenant_id, account_id)
    await db.commit()
    return stats


@router.get("/accounts/{account_id}/reconciliation-summary", response_model=ReconciliationSummary)
async def get_reconciliation_summary(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    summary = await svc.get_reconciliation_summary(account_id)
    return ReconciliationSummary(**summary)


# --- Statements ---

@router.get("/accounts/{account_id}/statements", response_model=list[BankStatementResponse])
async def list_statements(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    stmts = await svc.list_statements(account_id)
    return [BankStatementResponse(
        id=s.id, bank_account_id=s.bank_account_id,
        statement_date=s.statement_date, period_start=s.period_start,
        period_end=s.period_end, opening_balance=s.opening_balance,
        closing_balance=s.closing_balance, transaction_count=s.transaction_count,
        file_format=s.file_format, import_status=s.import_status,
        created_at=s.created_at,
    ) for s in stmts]


# --- Rules ---

@router.get("/rules", response_model=list[ReconciliationRuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    rules = await svc.list_rules(current_user.tenant_id)
    return [ReconciliationRuleResponse(
        id=r.id, name=r.name, description=r.description,
        match_criteria=r.match_criteria, target_account_code=r.target_account_code,
        target_journal_code=r.target_journal_code, auto_apply=r.auto_apply,
        priority=r.priority, is_active=r.is_active, created_at=r.created_at,
    ) for r in rules]


@router.post("/rules", response_model=ReconciliationRuleResponse)
async def create_rule(
    payload: ReconciliationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BankingService(db)
    rule = await svc.create_rule(
        current_user.tenant_id, current_user.id,
        **payload.model_dump(),
    )
    await db.commit()
    return ReconciliationRuleResponse(
        id=rule.id, name=rule.name, description=rule.description,
        match_criteria=rule.match_criteria, target_account_code=rule.target_account_code,
        target_journal_code=rule.target_journal_code, auto_apply=rule.auto_apply,
        priority=rule.priority, is_active=rule.is_active, created_at=rule.created_at,
    )
