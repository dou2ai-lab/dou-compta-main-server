"""
FINA Agent - SIG Calculator.
Computes Soldes Intermediaires de Gestion from trial balance data.
SIG is the French standard for income statement analysis.
"""
import structlog
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from services.accounting_service.models import JournalEntry, JournalEntryLine

logger = structlog.get_logger()


async def _sum_accounts(
    db: AsyncSession, tenant_id: UUID, fiscal_year: int,
    account_prefix: str, side: str = "credit"
) -> Decimal:
    """Sum amounts for accounts starting with prefix."""
    col = JournalEntryLine.credit if side == "credit" else JournalEntryLine.debit
    result = await db.execute(
        select(func.coalesce(func.sum(col), 0)).select_from(
            JournalEntryLine.__table__.join(
                JournalEntry.__table__,
                JournalEntryLine.entry_id == JournalEntry.id,
            )
        ).where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntry.fiscal_year == fiscal_year,
            JournalEntry.status.in_(["validated", "posted"]),
            JournalEntryLine.account_code.like(f"{account_prefix}%"),
        )
    )
    return result.scalar() or Decimal("0")


async def compute_sig(
    db: AsyncSession, tenant_id: UUID, fiscal_year: int
) -> dict:
    """
    Compute SIG (Soldes Intermediaires de Gestion).

    1. Marge commerciale = Ventes marchandises (707) - Achats marchandises (607)
    2. Production = Production vendue (70x) + Production stockee (71) + Production immobilisee (72)
    3. Valeur ajoutee = Marge + Production - Consommations externes (60-62)
    4. EBE = VA - Impots/taxes (63) - Charges personnel (64) + Subventions (74)
    5. Resultat exploitation = EBE + Autres produits (75-78) - Autres charges (65-68)
    6. Resultat financier = Produits financiers (76) - Charges financieres (66)
    7. Resultat courant = R. exploitation + R. financier
    8. Resultat exceptionnel = Produits except. (77) - Charges except. (67)
    9. Resultat net = R. courant + R. exceptionnel - Participation - IS
    """
    # Revenue
    ventes_marchandises = await _sum_accounts(db, tenant_id, fiscal_year, "707", "credit")
    production_vendue = await _sum_accounts(db, tenant_id, fiscal_year, "70", "credit")
    production_stockee = await _sum_accounts(db, tenant_id, fiscal_year, "71", "credit")
    production_immobilisee = await _sum_accounts(db, tenant_id, fiscal_year, "72", "credit")
    subventions = await _sum_accounts(db, tenant_id, fiscal_year, "74", "credit")

    # Costs
    achats_marchandises = await _sum_accounts(db, tenant_id, fiscal_year, "607", "debit")
    achats_mp = await _sum_accounts(db, tenant_id, fiscal_year, "60", "debit")
    services_ext = await _sum_accounts(db, tenant_id, fiscal_year, "61", "debit")
    autres_services = await _sum_accounts(db, tenant_id, fiscal_year, "62", "debit")
    impots_taxes = await _sum_accounts(db, tenant_id, fiscal_year, "63", "debit")
    charges_personnel = await _sum_accounts(db, tenant_id, fiscal_year, "64", "debit")
    autres_charges_gestion = await _sum_accounts(db, tenant_id, fiscal_year, "65", "debit")
    charges_financieres = await _sum_accounts(db, tenant_id, fiscal_year, "66", "debit")
    charges_except = await _sum_accounts(db, tenant_id, fiscal_year, "67", "debit")
    dotations = await _sum_accounts(db, tenant_id, fiscal_year, "68", "debit")

    # Other income
    autres_produits_gestion = await _sum_accounts(db, tenant_id, fiscal_year, "75", "credit")
    produits_financiers = await _sum_accounts(db, tenant_id, fiscal_year, "76", "credit")
    produits_except = await _sum_accounts(db, tenant_id, fiscal_year, "77", "credit")
    reprises = await _sum_accounts(db, tenant_id, fiscal_year, "78", "credit")

    # Compute SIG
    chiffre_affaires = production_vendue
    marge_commerciale = ventes_marchandises - achats_marchandises
    consommations = achats_mp + services_ext + autres_services
    valeur_ajoutee = marge_commerciale + (production_vendue - ventes_marchandises) + production_stockee + production_immobilisee - consommations
    ebe = valeur_ajoutee - impots_taxes - charges_personnel + subventions
    resultat_exploitation = ebe + autres_produits_gestion + reprises - autres_charges_gestion - dotations
    resultat_financier = produits_financiers - charges_financieres
    resultat_courant = resultat_exploitation + resultat_financier
    resultat_exceptionnel = produits_except - charges_except
    resultat_net = resultat_courant + resultat_exceptionnel

    result = {
        "fiscal_year": fiscal_year,
        "chiffre_affaires": str(chiffre_affaires),
        "marge_commerciale": str(marge_commerciale),
        "valeur_ajoutee": str(valeur_ajoutee),
        "ebe": str(ebe),
        "resultat_exploitation": str(resultat_exploitation),
        "resultat_financier": str(resultat_financier),
        "resultat_courant": str(resultat_courant),
        "resultat_exceptionnel": str(resultat_exceptionnel),
        "resultat_net": str(resultat_net),
    }

    logger.info("sig_computed", fiscal_year=fiscal_year, ca=str(chiffre_affaires), rn=str(resultat_net))
    return result
