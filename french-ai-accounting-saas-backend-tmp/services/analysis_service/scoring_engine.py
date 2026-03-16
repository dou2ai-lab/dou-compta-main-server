"""
Financial Health Scoring Engine.
Computes an overall health score (0-100) from financial ratios.
"""
import structlog
from decimal import Decimal
from typing import Optional

logger = structlog.get_logger()


def compute_score(sig: dict, ratios: dict) -> dict:
    """Compute financial health score from SIG and ratios."""
    components = {}

    # 1. Profitability (25 pts)
    marge = _to_decimal(ratios.get("marge_nette"))
    if marge is not None:
        if marge >= 10: components["profitability"] = 25
        elif marge >= 5: components["profitability"] = 20
        elif marge >= 2: components["profitability"] = 15
        elif marge >= 0: components["profitability"] = 8
        else: components["profitability"] = 0
    else:
        components["profitability"] = 10

    # 2. Liquidity (25 pts)
    liquidite = _to_decimal(ratios.get("ratio_liquidite"))
    if liquidite is not None:
        if liquidite >= 2: components["liquidity"] = 25
        elif liquidite >= 1.5: components["liquidity"] = 20
        elif liquidite >= 1: components["liquidity"] = 15
        elif liquidite >= 0.5: components["liquidity"] = 8
        else: components["liquidity"] = 0
    else:
        components["liquidity"] = 10

    # 3. Solvency (25 pts)
    endettement = _to_decimal(ratios.get("ratio_endettement"))
    if endettement is not None:
        if endettement <= 0.5: components["solvency"] = 25
        elif endettement <= 1: components["solvency"] = 20
        elif endettement <= 2: components["solvency"] = 12
        else: components["solvency"] = 5
    else:
        components["solvency"] = 10

    # 4. Activity (25 pts)
    ebe = _to_decimal(sig.get("ebe"))
    ca = _to_decimal(sig.get("chiffre_affaires"))
    if ebe is not None and ca is not None and ca > 0:
        ebe_ratio = float(ebe / ca * 100)
        if ebe_ratio >= 15: components["activity"] = 25
        elif ebe_ratio >= 8: components["activity"] = 20
        elif ebe_ratio >= 3: components["activity"] = 12
        else: components["activity"] = 5
    else:
        components["activity"] = 10

    overall = sum(components.values())

    if overall >= 80: category = "excellent"
    elif overall >= 60: category = "good"
    elif overall >= 40: category = "average"
    elif overall >= 20: category = "weak"
    else: category = "critical"

    recommendations = _generate_recommendations(sig, ratios, components)

    return {
        "overall_score": overall,
        "category": category,
        "components": components,
        "recommendations": recommendations,
    }


def _generate_recommendations(sig: dict, ratios: dict, components: dict) -> list[str]:
    recs = []
    if components.get("profitability", 0) < 15:
        recs.append("Ameliorer la marge nette en optimisant les couts ou en augmentant les prix.")
    if components.get("liquidity", 0) < 15:
        recs.append("Renforcer la tresorerie: reduire les delais clients ou negocier les delais fournisseurs.")
    if components.get("solvency", 0) < 15:
        recs.append("Reduire l'endettement ou augmenter les capitaux propres.")
    if components.get("activity", 0) < 15:
        recs.append("Ameliorer l'EBE en maitrisant les charges d'exploitation.")

    delai_clients = ratios.get("delai_clients")
    if delai_clients and int(delai_clients) > 60:
        recs.append(f"Delai clients eleve ({delai_clients}j). Relancer les impays.")

    return recs


def _to_decimal(val) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None
