"""
Configuration for the Accounting Service.
"""
import os

ACCOUNTING_SERVICE_PORT = int(os.getenv("ACCOUNTING_SERVICE_PORT", "8019"))

# French VAT rates (2025)
VAT_RATES = {
    "standard": 20.0,
    "intermediate": 10.0,
    "reduced": 5.5,
    "super_reduced": 2.1,
    "zero": 0.0,
}

# Journal codes
JOURNAL_CODES = {
    "ACH": "Journal des Achats",
    "VTE": "Journal des Ventes",
    "BNQ": "Journal de Banque",
    "OD": "Operations Diverses",
    "SAL": "Journal des Salaires",
    "AN": "A Nouveaux",
}

# PCG account class mapping
PCG_CLASSES = {
    1: "Comptes de capitaux",
    2: "Comptes d'immobilisations",
    3: "Comptes de stocks",
    4: "Comptes de tiers",
    5: "Comptes financiers",
    6: "Comptes de charges",
    7: "Comptes de produits",
    8: "Comptes speciaux",
}

# FEC column headers (Article A47 A-1)
FEC_COLUMNS = [
    "JournalCode",
    "JournalLib",
    "EcritureNum",
    "EcritureDate",
    "CompteNum",
    "CompteLib",
    "CompAuxNum",
    "CompAuxLib",
    "PieceRef",
    "PieceDate",
    "EcritureLib",
    "Debit",
    "Credit",
    "EcrtureLet",
    "DateLet",
    "ValidDate",
    "Montantdevise",
    "Idevise",
]
