"""
Financial Ratio Calculator.
Computes key French accounting ratios from trial balance.
"""
import structlog
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .sig_calculator import _sum_accounts

logger = structlog.get_logger()


async def compute_ratios(
    db: AsyncSession, tenant_id: UUID, fiscal_year: int
) -> dict:
    """Compute key financial ratios."""
    # Balance sheet items
    stocks = await _sum_accounts(db, tenant_id, fiscal_year, "3", "debit")
    creances_clients = await _sum_accounts(db, tenant_id, fiscal_year, "411", "debit")
    dettes_fournisseurs = await _sum_accounts(db, tenant_id, fiscal_year, "401", "credit")
    tresorerie_active = await _sum_accounts(db, tenant_id, fiscal_year, "5", "debit")
    emprunts = await _sum_accounts(db, tenant_id, fiscal_year, "16", "credit")
    capitaux_propres = await _sum_accounts(db, tenant_id, fiscal_year, "1", "credit")

    # P&L items
    ca = await _sum_accounts(db, tenant_id, fiscal_year, "70", "credit")
    achats = await _sum_accounts(db, tenant_id, fiscal_year, "60", "debit")
    resultat = await _sum_accounts(db, tenant_id, fiscal_year, "12", "credit")

    # BFR = Stocks + Creances clients - Dettes fournisseurs
    bfr = stocks + creances_clients - dettes_fournisseurs

    # Tresorerie nette
    tresorerie_nette = tresorerie_active - Decimal("0")  # Simplified

    # Ratio endettement = Dettes / Capitaux propres
    ratio_endettement = (emprunts / capitaux_propres) if capitaux_propres > 0 else None

    # Ratio liquidite = Actif circulant / Passif circulant
    actif_circulant = stocks + creances_clients + tresorerie_active
    ratio_liquidite = (actif_circulant / dettes_fournisseurs) if dettes_fournisseurs > 0 else None

    # Rotation stocks (days) = (Stocks / Achats) * 365
    rotation_stocks = int((stocks / achats * 365).quantize(Decimal("1"))) if achats > 0 else None

    # Delai clients (days) = (Creances / CA TTC) * 365
    delai_clients = int((creances_clients / (ca * Decimal("1.2")) * 365).quantize(Decimal("1"))) if ca > 0 else None

    # Delai fournisseurs (days) = (Dettes fourn / Achats TTC) * 365
    delai_fournisseurs = int((dettes_fournisseurs / (achats * Decimal("1.2")) * 365).quantize(Decimal("1"))) if achats > 0 else None

    # Marge nette = Resultat / CA
    marge_nette = (resultat / ca * 100) if ca > 0 else None

    # Rentabilite capitaux propres = Resultat / Capitaux propres
    rentabilite = (resultat / capitaux_propres * 100) if capitaux_propres > 0 else None

    return {
        "fiscal_year": fiscal_year,
        "bfr": str(bfr),
        "tresorerie_nette": str(tresorerie_nette),
        "ratio_endettement": str(ratio_endettement) if ratio_endettement else None,
        "ratio_liquidite": str(ratio_liquidite) if ratio_liquidite else None,
        "rotation_stocks": rotation_stocks,
        "delai_clients": delai_clients,
        "delai_fournisseurs": delai_fournisseurs,
        "marge_nette": str(marge_nette) if marge_nette else None,
        "rentabilite_capitaux": str(rentabilite) if rentabilite else None,
    }
