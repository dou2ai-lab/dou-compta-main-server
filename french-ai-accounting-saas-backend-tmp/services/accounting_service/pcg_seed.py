"""
PCG 2025 (Plan Comptable General) seed data.
Provides the standard chart of accounts for French accounting.
"""
import structlog
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .models import PCGAccount

logger = structlog.get_logger()


def get_pcg_seed_data() -> list[dict]:
    """Return seed data for ~100 core PCG 2025 accounts across all 8 classes."""
    return [
        # ===== CLASS 1: Comptes de capitaux =====
        {"account_code": "101000", "account_name": "Capital", "account_class": 1, "account_type": "equity", "parent_code": None},
        {"account_code": "106000", "account_name": "Reserves", "account_class": 1, "account_type": "equity", "parent_code": None},
        {"account_code": "106100", "account_name": "Reserve legale", "account_class": 1, "account_type": "equity", "parent_code": "106000"},
        {"account_code": "106800", "account_name": "Autres reserves", "account_class": 1, "account_type": "equity", "parent_code": "106000"},
        {"account_code": "108000", "account_name": "Compte de l'exploitant", "account_class": 1, "account_type": "equity", "parent_code": None},
        {"account_code": "110000", "account_name": "Report a nouveau", "account_class": 1, "account_type": "equity", "parent_code": None},
        {"account_code": "119000", "account_name": "Report a nouveau (solde debiteur)", "account_class": 1, "account_type": "equity", "parent_code": "110000"},
        {"account_code": "120000", "account_name": "Resultat de l'exercice (benefice)", "account_class": 1, "account_type": "equity", "parent_code": None},
        {"account_code": "129000", "account_name": "Resultat de l'exercice (perte)", "account_class": 1, "account_type": "equity", "parent_code": "120000"},
        {"account_code": "164000", "account_name": "Emprunts aupres des etablissements de credit", "account_class": 1, "account_type": "liability", "parent_code": None},
        {"account_code": "165000", "account_name": "Depots et cautionnements recus", "account_class": 1, "account_type": "liability", "parent_code": None},

        # ===== CLASS 2: Comptes d'immobilisations =====
        {"account_code": "201000", "account_name": "Frais d'etablissement", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "205000", "account_name": "Concessions, brevets et droits similaires", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "206000", "account_name": "Droit au bail", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "207000", "account_name": "Fonds commercial", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "211000", "account_name": "Terrains", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "213000", "account_name": "Constructions", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "215400", "account_name": "Materiel industriel", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "218200", "account_name": "Materiel de transport", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "218300", "account_name": "Materiel de bureau et informatique", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "218400", "account_name": "Mobilier", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "231000", "account_name": "Immobilisations corporelles en cours", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "275000", "account_name": "Depots et cautionnements verses", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "280000", "account_name": "Amortissements des immobilisations incorporelles", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "281000", "account_name": "Amortissements des immobilisations corporelles", "account_class": 2, "account_type": "asset", "parent_code": None},
        {"account_code": "281300", "account_name": "Amortissements des constructions", "account_class": 2, "account_type": "asset", "parent_code": "281000"},
        {"account_code": "281540", "account_name": "Amortissements du materiel industriel", "account_class": 2, "account_type": "asset", "parent_code": "281000"},
        {"account_code": "281820", "account_name": "Amortissements du materiel de transport", "account_class": 2, "account_type": "asset", "parent_code": "281000"},
        {"account_code": "281830", "account_name": "Amortissements du materiel de bureau et informatique", "account_class": 2, "account_type": "asset", "parent_code": "281000"},

        # ===== CLASS 3: Comptes de stocks =====
        {"account_code": "310000", "account_name": "Matieres premieres", "account_class": 3, "account_type": "asset", "parent_code": None},
        {"account_code": "355000", "account_name": "Produits finis", "account_class": 3, "account_type": "asset", "parent_code": None},
        {"account_code": "370000", "account_name": "Stocks de marchandises", "account_class": 3, "account_type": "asset", "parent_code": None},
        {"account_code": "391000", "account_name": "Provisions pour depreciation des matieres premieres", "account_class": 3, "account_type": "asset", "parent_code": None},
        {"account_code": "397000", "account_name": "Provisions pour depreciation des stocks de marchandises", "account_class": 3, "account_type": "asset", "parent_code": None},

        # ===== CLASS 4: Comptes de tiers =====
        {"account_code": "401000", "account_name": "Fournisseurs", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "401100", "account_name": "Fournisseurs - Achats de biens", "account_class": 4, "account_type": "liability", "parent_code": "401000"},
        {"account_code": "401200", "account_name": "Fournisseurs - Prestations de services", "account_class": 4, "account_type": "liability", "parent_code": "401000"},
        {"account_code": "403000", "account_name": "Fournisseurs - Effets a payer", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "404000", "account_name": "Fournisseurs d'immobilisations", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "408000", "account_name": "Fournisseurs - Factures non parvenues", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "411000", "account_name": "Clients", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "413000", "account_name": "Clients - Effets a recevoir", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "416000", "account_name": "Clients douteux ou litigieux", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "418000", "account_name": "Clients - Produits non encore factures", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "421000", "account_name": "Personnel - Remunerations dues", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "425000", "account_name": "Personnel - Avances et acomptes", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "431000", "account_name": "Securite sociale", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "437000", "account_name": "Autres organismes sociaux", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "440000", "account_name": "Etat et autres collectivites publiques", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "444000", "account_name": "Etat - Impots sur les benefices", "account_class": 4, "account_type": "liability", "parent_code": "440000"},
        {"account_code": "445660", "account_name": "TVA deductible sur autres biens et services", "account_class": 4, "account_type": "asset", "parent_code": "440000"},
        {"account_code": "445670", "account_name": "Credit de TVA", "account_class": 4, "account_type": "asset", "parent_code": "440000"},
        {"account_code": "445710", "account_name": "TVA collectee", "account_class": 4, "account_type": "liability", "parent_code": "440000"},
        {"account_code": "445800", "account_name": "TVA a regulariser", "account_class": 4, "account_type": "liability", "parent_code": "440000"},
        {"account_code": "455000", "account_name": "Associes - Comptes courants", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "467000", "account_name": "Autres comptes debiteurs ou crediteurs", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "471000", "account_name": "Comptes d'attente", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "486000", "account_name": "Charges constatees d'avance", "account_class": 4, "account_type": "asset", "parent_code": None},
        {"account_code": "487000", "account_name": "Produits constates d'avance", "account_class": 4, "account_type": "liability", "parent_code": None},
        {"account_code": "491000", "account_name": "Provisions pour depreciation des comptes clients", "account_class": 4, "account_type": "asset", "parent_code": None},

        # ===== CLASS 5: Comptes financiers =====
        {"account_code": "512000", "account_name": "Banques", "account_class": 5, "account_type": "asset", "parent_code": None},
        {"account_code": "514000", "account_name": "Cheques postaux", "account_class": 5, "account_type": "asset", "parent_code": None},
        {"account_code": "530000", "account_name": "Caisse", "account_class": 5, "account_type": "asset", "parent_code": None},
        {"account_code": "580000", "account_name": "Virements internes", "account_class": 5, "account_type": "asset", "parent_code": None},
        {"account_code": "590000", "account_name": "Provisions pour depreciation des comptes financiers", "account_class": 5, "account_type": "asset", "parent_code": None},

        # ===== CLASS 6: Comptes de charges =====
        {"account_code": "601000", "account_name": "Achats de matieres premieres", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "602200", "account_name": "Fournitures consommables", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "604000", "account_name": "Achats d'etudes et prestations de services", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "606100", "account_name": "Fournitures non stockables (eau, energie)", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "606400", "account_name": "Fournitures administratives", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "607000", "account_name": "Achats de marchandises", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "609000", "account_name": "Rabais, remises et ristournes obtenus sur achats", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "611000", "account_name": "Sous-traitance generale", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "613200", "account_name": "Locations immobilieres", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "613500", "account_name": "Locations mobilieres", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "615000", "account_name": "Entretien et reparations", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "616000", "account_name": "Primes d'assurances", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "622600", "account_name": "Honoraires", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "623400", "account_name": "Cadeaux a la clientele", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "625100", "account_name": "Voyages et deplacements", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "625600", "account_name": "Missions", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "625700", "account_name": "Receptions", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "626000", "account_name": "Frais postaux et de telecommunications", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "627000", "account_name": "Services bancaires et assimiles", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "628000", "account_name": "Divers", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "631000", "account_name": "Impots, taxes et versements assimiles sur remunerations", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "635000", "account_name": "Autres impots, taxes et versements assimiles", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "641100", "account_name": "Salaires, appointements", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "645100", "account_name": "Cotisations a l'URSSAF", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "645300", "account_name": "Cotisations aux caisses de retraite", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "661000", "account_name": "Charges d'interets", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "671000", "account_name": "Charges exceptionnelles sur operations de gestion", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "675000", "account_name": "Valeurs comptables des elements d'actif cedes", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "681000", "account_name": "Dotations aux amortissements et provisions - charges d'exploitation", "account_class": 6, "account_type": "expense", "parent_code": None},
        {"account_code": "695000", "account_name": "Impots sur les benefices", "account_class": 6, "account_type": "expense", "parent_code": None},

        # ===== CLASS 7: Comptes de produits =====
        {"account_code": "701000", "account_name": "Ventes de produits finis", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "706000", "account_name": "Prestations de services", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "707000", "account_name": "Ventes de marchandises", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "708500", "account_name": "Ports et frais accessoires factures", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "709000", "account_name": "Rabais, remises et ristournes accordes", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "740000", "account_name": "Subventions d'exploitation", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "755000", "account_name": "Quotes-parts de resultat sur operations faites en commun", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "771000", "account_name": "Produits exceptionnels sur operations de gestion", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "775000", "account_name": "Produits des cessions d'elements d'actif", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "781000", "account_name": "Reprises sur amortissements et provisions", "account_class": 7, "account_type": "revenue", "parent_code": None},
        {"account_code": "791000", "account_name": "Transferts de charges d'exploitation", "account_class": 7, "account_type": "revenue", "parent_code": None},

        # ===== CLASS 8: Comptes speciaux =====
        {"account_code": "890000", "account_name": "Bilan d'ouverture", "account_class": 8, "account_type": "equity", "parent_code": None},
    ]


async def seed_pcg_accounts(db: AsyncSession, tenant_id: UUID) -> None:
    """
    Seed PCG accounts for a tenant if none exist.
    Checks for existing accounts before inserting to avoid duplicates.
    """
    # Check if accounts already exist for this tenant
    result = await db.execute(
        select(func.count(PCGAccount.id)).where(
            PCGAccount.tenant_id == tenant_id,
        )
    )
    existing_count = result.scalar() or 0

    if existing_count > 0:
        logger.info(
            "pcg_seed_skipped",
            tenant_id=str(tenant_id),
            existing_count=existing_count,
        )
        return

    seed_data = get_pcg_seed_data()

    for entry in seed_data:
        account = PCGAccount(
            id=uuid4(),
            tenant_id=tenant_id,
            account_code=entry["account_code"],
            account_name=entry["account_name"],
            account_class=entry["account_class"],
            account_type=entry["account_type"],
            parent_code=entry.get("parent_code"),
            is_system=True,
            is_active=True,
        )
        db.add(account)

    await db.flush()

    logger.info(
        "pcg_seed_complete",
        tenant_id=str(tenant_id),
        accounts_created=len(seed_data),
    )
