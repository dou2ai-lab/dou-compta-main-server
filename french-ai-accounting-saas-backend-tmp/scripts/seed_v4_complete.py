"""
Supplementary seed script for V4 tables - covers ALL modules not yet seeded.
Populates: additional expenses, expense reports, risk scores, audit trails,
notifications, expense policies, categories, VAT rules, tax declarations,
bank transactions, and financial snapshots.

Usage: python scripts/seed_v4_complete.py
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://dou_user:dou_password123@localhost:5433/dou_expense_audit"


def uid():
    """Generate a new UUID4."""
    return uuid.uuid4()


async def table_exists(db, table_name: str) -> bool:
    """Check if a table exists in the database."""
    row = (await db.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
    ), {"t": table_name})).fetchone()
    return row[0] if row else False


async def get_count(db, table_name: str, tenant_id=None) -> int:
    """Get row count from a table, optionally filtered by tenant."""
    if tenant_id:
        row = (await db.execute(text(
            f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id = :tid"
        ), {"tid": tenant_id})).fetchone()
    else:
        row = (await db.execute(text(
            f"SELECT COUNT(*) FROM {table_name}"
        ), {})).fetchone()
    return row[0] if row else 0


async def seed_v4_complete():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # ------------------------------------------------------------------
            # Fetch tenant_id and user_id
            # ------------------------------------------------------------------
            print("[INIT] Fetching tenant and admin user...")
            row = (await db.execute(text("SELECT id FROM tenants LIMIT 1"))).fetchone()
            if not row:
                print("ERROR: No tenant found. Run seed_data.py / seed_v4_data.py first.")
                return
            tenant_id = row[0]
            print(f"  Tenant ID: {tenant_id}")

            row = (await db.execute(text(
                "SELECT id FROM users WHERE email = 'admin@doucompta.fr'"
            ))).fetchone()
            if not row:
                row = (await db.execute(text("SELECT id FROM users LIMIT 1"))).fetchone()
            if not row:
                print("ERROR: No user found. Run seed_data.py first.")
                return
            user_id = row[0]
            print(f"  User  ID: {user_id}")

            # Try to get a dossier_id for tax declarations
            dossier_row = (await db.execute(text(
                "SELECT id FROM client_dossiers WHERE tenant_id = :tid LIMIT 1"
            ), {"tid": tenant_id})).fetchone()
            dossier_id = dossier_row[0] if dossier_row else None

            # Try to get a bank_account_id
            bank_row = (await db.execute(text(
                "SELECT id FROM bank_accounts WHERE tenant_id = :tid LIMIT 1"
            ), {"tid": tenant_id})).fetchone()
            bank_account_id = bank_row[0] if bank_row else None

            # ==================================================================
            # [1/11] More Expenses (add 5 if total < 10)
            # ==================================================================
            print("[1/11] Seeding additional expenses...")
            expense_count = await get_count(db, "expenses", tenant_id)
            if expense_count < 10:
                extra_expenses = [
                    (Decimal("67.50"),  date(2026, 1, 18), "repas",        "Restaurant Le Bistrot",       "Le Bistrot",       "approved",  "approved", Decimal("6.14"),  Decimal("10.00")),
                    (Decimal("45.00"),  date(2026, 2, 5),  "transport",    "Taxi Aeroport CDG",           "Taxi G7",          "approved",  "approved", Decimal("4.09"),  Decimal("10.00")),
                    (Decimal("32.80"),  date(2026, 2, 12), "fournitures",  "Papeterie Bureau",            "Papeterie Martin", "submitted", None,       Decimal("5.47"),  Decimal("20.00")),
                    (Decimal("39.99"),  date(2026, 2, 20), "telecom",      "Abonnement SFR Pro",          "SFR",              "draft",     None,       Decimal("6.67"),  Decimal("20.00")),
                    (Decimal("112.00"), date(2026, 3, 2),  "voyage",       "Deplacement Lyon TGV",        "SNCF",             "approved",  "approved", Decimal("10.18"), Decimal("10.00")),
                ]
                for amt, exp_date, cat, desc, merchant, status, appr_status, vat_amt, vat_r in extra_expenses:
                    await db.execute(text("""
                        INSERT INTO expenses
                            (id, tenant_id, submitted_by, amount, currency, expense_date,
                             category, description, merchant_name, status, approval_status,
                             vat_amount, vat_rate, policy_violation_count, has_policy_violations,
                             created_at, updated_at)
                        VALUES
                            (:id, :tid, :uid, :amt, 'EUR', :ed,
                             :cat, :desc, :merch, :st, :ast,
                             :va, :vr, 0, false,
                             NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id, "uid": user_id,
                        "amt": amt, "ed": exp_date,
                        "cat": cat, "desc": desc, "merch": merchant,
                        "st": status, "ast": appr_status,
                        "va": vat_amt, "vr": vat_r,
                    })
                print(f"  Added 5 expenses (was {expense_count}, target >= 10).")
            else:
                print(f"  Skipped -- already {expense_count} expenses.")

            # ==================================================================
            # [2/11] Expense Reports (finance dashboard data)
            # ==================================================================
            print("[2/11] Seeding expense reports...")
            reports_data = [
                ("NF-RPT-2026-001", "Rapport Janvier 2026",  date(2026, 1, 1),  date(2026, 1, 31), "approved",  "approved",  Decimal("1245.50"), 4),
                ("NF-RPT-2026-002", "Rapport Fevrier 2026",  date(2026, 2, 1),  date(2026, 2, 28), "submitted", None,        Decimal("890.75"),  3),
                ("NF-RPT-2026-003", "Rapport Mars 2026",     date(2026, 3, 1),  date(2026, 3, 31), "draft",     None,        Decimal("567.20"),  2),
            ]
            for rpt_num, title, p_start, p_end, status, appr, total, exp_cnt in reports_data:
                await db.execute(text("""
                    INSERT INTO expense_reports
                        (id, tenant_id, submitted_by, report_number, report_type,
                         title, period_start_date, period_end_date, period_type,
                         total_amount, currency, expense_count,
                         status, approval_status,
                         created_at, updated_at)
                    VALUES
                        (:id, :tid, :uid, :rn, 'period',
                         :title, :ps, :pe, 'monthly',
                         :total, 'EUR', :cnt,
                         :st, :ast,
                         NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": uid(), "tid": tenant_id, "uid": user_id,
                    "rn": rpt_num, "title": title,
                    "ps": p_start, "pe": p_end,
                    "total": total, "cnt": exp_cnt,
                    "st": status, "ast": appr,
                })
            print(f"  Inserted/skipped {len(reports_data)} expense reports.")

            # ==================================================================
            # [3/11] Anomaly / Risk Score Data
            # ==================================================================
            print("[3/11] Seeding risk scores...")
            if await table_exists(db, "risk_scores"):
                risk_entries = [
                    ("employee",     str(user_id),  Decimal("0.8500")),
                    ("merchant",     str(uid()),    Decimal("0.6200")),
                    ("expense_line", str(uid()),    Decimal("0.3100")),
                ]
                for etype, eid, score in risk_entries:
                    await db.execute(text("""
                        INSERT INTO risk_scores
                            (id, tenant_id, entity_type, entity_id, risk_score, updated_at)
                        VALUES
                            (:id, :tid, :et, :eid, :rs, NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id,
                        "et": etype, "eid": eid, "rs": score,
                    })
                print(f"  Inserted/skipped {len(risk_entries)} risk scores.")
            else:
                print("  risk_scores table not found -- skipped.")

            # ==================================================================
            # [4/11] Audit Data (audit_trails)
            # ==================================================================
            print("[4/11] Seeding audit trail entries...")
            if await table_exists(db, "audit_trails"):
                audit_entries = [
                    ("expense",  str(uid()), "create",  {"description": "Expense created: Restaurant Le Bistrot 67.50 EUR"}),
                    ("expense",  str(uid()), "approve", {"description": "Expense approved by manager", "approver": "admin@doucompta.fr"}),
                    ("settings", str(uid()), "update",  {"description": "TVA regime updated for dossier", "field": "regime_tva", "old": "reel_simplifie", "new": "reel_normal"}),
                ]
                for entity_type, entity_id, action, meta in audit_entries:
                    await db.execute(text("""
                        INSERT INTO audit_trails
                            (id, tenant_id, entity_type, entity_id, action,
                             performed_by, performed_at, metadata)
                        VALUES
                            (:id, :tid, :et, :eid, :act,
                             :uid, NOW(), :meta)
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id,
                        "et": entity_type, "eid": entity_id, "act": action,
                        "uid": user_id, "meta": json.dumps(meta),
                    })
                print(f"  Inserted/skipped {len(audit_entries)} audit trail entries.")
            else:
                print("  audit_trails table not found -- skipped.")

            # ==================================================================
            # [5/11] More Notifications (add 5 more if < 10)
            # ==================================================================
            print("[5/11] Seeding additional notifications...")
            notif_count = await get_count(db, "notifications", tenant_id)
            if notif_count < 10:
                extra_notifs = [
                    ("reconciliation.completed", "Rapprochement bancaire termine",
                     "Le rapprochement automatique a identifie 8 transactions sur 10 pour le compte BNP Paribas.",
                     "normal", "/banking/reconciliation"),
                    ("expense.rejected", "Note de frais rejetee",
                     "Votre note de frais NF-2026-005 de 78.50 EUR a ete rejetee. Motif: justificatif manquant.",
                     "high", "/expenses"),
                    ("expense.submitted", "Nouvelle note de frais soumise",
                     "Jean Dupont a soumis une note de frais de 32.80 EUR (Papeterie Bureau) pour approbation.",
                     "normal", "/expenses/pending"),
                    ("entry.created", "Ecriture comptable generee",
                     "L'ecriture ACH-2026-0011 (Deplacement Lyon TGV - 112.00 EUR) a ete comptabilisee automatiquement.",
                     "normal", "/accounting/entries"),
                    ("entry.created", "Ecriture comptable generee",
                     "L'ecriture ACH-2026-0012 (Abonnement SFR Pro - 39.99 EUR) a ete comptabilisee automatiquement.",
                     "normal", "/accounting/entries"),
                ]
                for ntype, title, body, priority, action_url in extra_notifs:
                    await db.execute(text("""
                        INSERT INTO notifications
                            (id, tenant_id, user_id, type, title, body,
                             channel, status, priority, action_url,
                             created_at, updated_at)
                        VALUES
                            (:id, :tid, :uid, :tp, :tl, :bd,
                             'in_app', 'unread', :pr, :au,
                             NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id, "uid": user_id,
                        "tp": ntype, "tl": title, "bd": body,
                        "pr": priority, "au": action_url,
                    })
                print(f"  Added 5 notifications (was {notif_count}, target >= 10).")
            else:
                print(f"  Skipped -- already {notif_count} notifications.")

            # ==================================================================
            # [6/11] Admin Expense Policies
            # ==================================================================
            print("[6/11] Seeding expense policies...")
            if await table_exists(db, "expense_policies"):
                policies = [
                    (
                        "Plafond repas",
                        "Limite de 25 EUR par repas individuel (hors invitation client)",
                        "amount_limit",
                        {"max_amount": 25, "currency": "EUR", "category": "repas", "scope": "per_meal"},
                        ["employee"],
                    ),
                    (
                        "Approbation manager",
                        "Toute depense superieure a 200 EUR necessite l'approbation du manager",
                        "approval_required",
                        {"threshold_amount": 200, "currency": "EUR", "approval_level": "manager"},
                        ["employee"],
                    ),
                    (
                        "Deplacement international",
                        "Les deplacements internationaux necessitent une pre-approbation avant reservation",
                        "pre_approval",
                        {"scope": "international_travel", "requires_pre_approval": True, "approval_level": "director"},
                        ["employee", "approver"],
                    ),
                ]
                for name, desc, ptype, rules, roles in policies:
                    await db.execute(text("""
                        INSERT INTO expense_policies
                            (id, tenant_id, name, description, policy_type,
                             policy_rules, applies_to_roles, is_active,
                             created_by, created_at, updated_at)
                        VALUES
                            (:id, :tid, :nm, :desc, :pt,
                             :rules, :roles, true,
                             :uid, NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id,
                        "nm": name, "desc": desc, "pt": ptype,
                        "rules": json.dumps(rules), "roles": json.dumps(roles),
                        "uid": user_id,
                    })
                print(f"  Inserted/skipped {len(policies)} expense policies.")
            else:
                print("  expense_policies table not found -- skipped.")

            # ==================================================================
            # [7/11] Expense Categories with GL Account links
            # ==================================================================
            print("[7/11] Seeding expense categories...")
            if await table_exists(db, "expense_categories") and await table_exists(db, "gl_accounts"):
                categories = [
                    ("Repas & Restaurants",       "REPAS",   "625700", "Frais de repas et restauration"),
                    ("Transport & Deplacements",  "TRANSP",  "625100", "Frais de transport et deplacement"),
                    ("Hebergement",               "HOTEL",   "625600", "Frais d'hebergement et hotel"),
                    ("Fournitures de bureau",     "FOURN",   "606400", "Fournitures et petit materiel de bureau"),
                    ("Telecommunications",        "TELECOM", "626000", "Telephonie, internet et services telecom"),
                    ("Honoraires & Consulting",   "HONOR",   "622600", "Honoraires et frais de conseil"),
                    ("Assurances",                "ASSUR",   "616000", "Primes d'assurance"),
                    ("Loyers & Charges",          "LOYER",   "613200", "Loyers immobiliers et charges locatives"),
                    ("Informatique & Logiciels",  "INFO",    "218300", "Materiel informatique et licences logicielles"),
                    ("Frais bancaires",           "BANK",    "627000", "Frais et commissions bancaires"),
                ]
                for cat_name, code, gl_code, desc in categories:
                    # First create GL account if not exists
                    gl_id = uid()
                    await db.execute(text("""
                        INSERT INTO gl_accounts
                            (id, tenant_id, account_code, account_name, account_type,
                             description, is_active, created_at, updated_at)
                        VALUES
                            (:id, :tid, :code, :name, 'expense',
                             :desc, true, NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": gl_id, "tid": tenant_id,
                        "code": gl_code, "name": cat_name, "desc": desc,
                    })
                    # Fetch actual GL account id (may already exist)
                    gl_row = (await db.execute(text(
                        "SELECT id FROM gl_accounts WHERE tenant_id = :tid AND account_code = :code LIMIT 1"
                    ), {"tid": tenant_id, "code": gl_code})).fetchone()
                    actual_gl_id = gl_row[0] if gl_row else gl_id

                    await db.execute(text("""
                        INSERT INTO expense_categories
                            (id, tenant_id, name, code, description,
                             gl_account_id, is_active, created_at, updated_at)
                        VALUES
                            (:id, :tid, :name, :code, :desc,
                             :glid, true, NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id,
                        "name": cat_name, "code": code, "desc": desc,
                        "glid": actual_gl_id,
                    })
                print(f"  Inserted/skipped {len(categories)} categories with GL links.")
            else:
                print("  expense_categories or gl_accounts table not found -- skipped.")

            # ==================================================================
            # [8/11] VAT Rules
            # ==================================================================
            print("[8/11] Seeding VAT rules...")
            if await table_exists(db, "vat_rules"):
                vat_rules = [
                    ("Restauration",         "repas|restaurant",                 Decimal("10.00"), "TVA10-REST",  False),
                    ("Transport voyageurs",  "transport|train|taxi",             Decimal("10.00"), "TVA10-TRANS", False),
                    ("Standard",             "fournitures|telecom|honoraires",   Decimal("20.00"), "TVA20-STD",   True),
                    ("Alimentaire",          "alimentaire|nourriture",           Decimal("5.50"),  "TVA55-ALIM",  False),
                ]
                for cat, pattern, rate, vat_code, is_default in vat_rules:
                    await db.execute(text("""
                        INSERT INTO vat_rules
                            (id, tenant_id, category, merchant_pattern,
                             vat_rate, vat_code, is_default,
                             created_at, updated_at)
                        VALUES
                            (:id, :tid, :cat, :pat,
                             :rate, :code, :dflt,
                             NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id,
                        "cat": cat, "pat": pattern,
                        "rate": rate, "code": vat_code, "dflt": is_default,
                    })
                print(f"  Inserted/skipped {len(vat_rules)} VAT rules.")
            else:
                print("  vat_rules table not found -- skipped.")

            # ==================================================================
            # [9/11] Tax Declarations (CA3)
            # ==================================================================
            print("[9/11] Seeding tax declarations...")
            if await table_exists(db, "tax_declarations"):
                declarations = [
                    (
                        "CA3", date(2026, 1, 1), date(2026, 1, 31), date(2026, 2, 24),
                        "validated", Decimal("1250.00"),
                        {
                            "tva_collected": "3250.00",
                            "tva_deductible": "2000.00",
                            "tva_due": "1250.00",
                            "base_ht_ventes": "16250.00",
                            "base_ht_achats": "10000.00",
                            "tva_rates": {"20.0": {"collected": "2500.00", "deductible": "1600.00"}, "10.0": {"collected": "750.00", "deductible": "400.00"}}
                        },
                    ),
                    (
                        "CA3", date(2026, 2, 1), date(2026, 2, 28), date(2026, 3, 24),
                        "computed", Decimal("890.00"),
                        {
                            "tva_collected": "2340.00",
                            "tva_deductible": "1450.00",
                            "tva_due": "890.00",
                            "base_ht_ventes": "11700.00",
                            "base_ht_achats": "7250.00",
                            "tva_rates": {"20.0": {"collected": "1800.00", "deductible": "1100.00"}, "10.0": {"collected": "540.00", "deductible": "350.00"}}
                        },
                    ),
                ]
                for decl_type, ps, pe, due, status, total, computed in declarations:
                    await db.execute(text("""
                        INSERT INTO tax_declarations
                            (id, tenant_id, dossier_id, type,
                             period_start, period_end, due_date,
                             status, total_amount, computed_data,
                             created_at, updated_at)
                        VALUES
                            (:id, :tid, :did, :tp,
                             :ps, :pe, :dd,
                             :st, :total, :cd,
                             NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "tid": tenant_id, "did": dossier_id,
                        "tp": decl_type, "ps": ps, "pe": pe, "dd": due,
                        "st": status, "total": total,
                        "cd": json.dumps(computed),
                    })
                print(f"  Inserted/skipped {len(declarations)} tax declarations.")
            else:
                print("  tax_declarations table not found -- skipped.")

            # ==================================================================
            # [10/11] More Bank Transactions (add 10 if total < 20)
            # ==================================================================
            print("[10/11] Seeding additional bank transactions...")
            if bank_account_id:
                txn_count = await get_count(db, "bank_transactions")
                if txn_count < 20:
                    # 5 matched, 3 unmatched, 2 ignored
                    extra_txns = [
                        (date(2026, 3, 1),  Decimal("-1500.00"), "VIR LOYER MARS BUREAU 3EME",              "VIR-2026-005", "SCI IMMOBILIERE PARIS",  "virement",       "loyer",          "matched"),
                        (date(2026, 3, 3),  Decimal("-67.50"),   "CB LE BISTROT PARIS 15",                  "CB-2026-005",  "Le Bistrot",             "carte_bancaire", "restauration",   "matched"),
                        (date(2026, 3, 5),  Decimal("-45.00"),   "CB TAXI G7 ROISSY CDG",                   "CB-2026-006",  "Taxi G7",                "carte_bancaire", "transport",      "matched"),
                        (date(2026, 3, 8),  Decimal("15200.00"), "VIR CLIENT ALPHA SAS FAC-2026-02",        "VIR-2026-006", "Client Alpha SAS",       "virement",       "encaissement",   "matched"),
                        (date(2026, 3, 10), Decimal("-112.00"),  "CB SNCF BILLET TGV LYON",                 "CB-2026-007",  "SNCF",                   "carte_bancaire", "transport",      "matched"),
                        (date(2026, 3, 12), Decimal("-250.00"),  "CB AMAZON BUSINESS FR",                   "CB-2026-008",  "Amazon Business",        "carte_bancaire", "fournitures",    "unmatched"),
                        (date(2026, 3, 14), Decimal("-89.99"),   "PRLV MICROSOFT 365 BUSINESS",             "PRLV-2026-003","Microsoft",              "prelevement",    "informatique",   "unmatched"),
                        (date(2026, 3, 15), Decimal("-175.00"),  "CB NOVOTEL LYON PART DIEU",               "CB-2026-009",  "Novotel Lyon",           "carte_bancaire", "hotel",          "unmatched"),
                        (date(2026, 3, 2),  Decimal("-3.50"),    "FRAIS TENUE COMPTE MARS",                 "FRS-2026-001", "BNP Paribas",            "frais",          "frais_bancaires","ignored"),
                        (date(2026, 3, 7),  Decimal("-0.15"),    "COMMISSION VIREMENT SEPA",                "FRS-2026-002", "BNP Paribas",            "frais",          "frais_bancaires","ignored"),
                    ]
                    for txn_date, amount, label, ref, counterparty, txn_type, cat, recon_status in extra_txns:
                        await db.execute(text("""
                            INSERT INTO bank_transactions
                                (id, bank_account_id, transaction_date, value_date, amount,
                                 currency, label, reference, counterparty_name,
                                 transaction_type, category, reconciliation_status,
                                 created_at, updated_at)
                            VALUES
                                (:id, :baid, :td, :vd, :amt,
                                 'EUR', :lbl, :ref, :cp,
                                 :tt, :cat, :rs,
                                 NOW(), NOW())
                            ON CONFLICT DO NOTHING
                        """), {
                            "id": uid(), "baid": bank_account_id,
                            "td": txn_date, "vd": txn_date,
                            "amt": amount, "lbl": label, "ref": ref,
                            "cp": counterparty, "tt": txn_type, "cat": cat,
                            "rs": recon_status,
                        })
                    print(f"  Added 10 bank transactions (was {txn_count}, target >= 20).")
                else:
                    print(f"  Skipped -- already {txn_count} bank transactions.")
            else:
                print("  No bank account found -- skipped.")

            # ==================================================================
            # [11/11] Financial Snapshots
            # ==================================================================
            print("[11/11] Seeding financial snapshots...")
            if await table_exists(db, "financial_snapshots"):
                sig_data = {
                    "chiffre_affaires": "500000",
                    "marge_commerciale": "150000",
                    "valeur_ajoutee": "200000",
                    "ebe": "80000",
                    "resultat_exploitation": "60000",
                    "resultat_net": "45000",
                }
                ratios = {
                    "bfr": "25000",
                    "tresorerie_nette": "75000",
                    "ratio_endettement": "0.45",
                    "ratio_liquidite": "2.1",
                    "marge_nette": "9.0",
                    "delai_clients": 35,
                    "delai_fournisseurs": 42,
                }
                scoring = {
                    "overall_score": 72,
                    "category": "good",
                    "components": {
                        "profitability": 20,
                        "liquidity": 20,
                        "solvency": 20,
                        "activity": 12,
                    },
                    "recommendations": ["Ameliorer la marge nette"],
                }
                await db.execute(text("""
                    INSERT INTO financial_snapshots
                        (id, tenant_id, dossier_id, snapshot_date, fiscal_year,
                         sig_data, ratios, scoring, created_at)
                    VALUES
                        (:id, :tid, :did, :sd, :fy,
                         :sig, :rat, :sc, NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": uid(), "tid": tenant_id, "did": dossier_id,
                    "sd": date(2025, 12, 31), "fy": 2025,
                    "sig": json.dumps(sig_data),
                    "rat": json.dumps(ratios),
                    "sc": json.dumps(scoring),
                })
                print("  Inserted/skipped 1 financial snapshot (FY 2025).")
            else:
                print("  financial_snapshots table not found -- skipped.")

            # ------------------------------------------------------------------
            # Commit everything
            # ------------------------------------------------------------------
            await db.commit()
            print("")
            print("=" * 60)
            print("  V4 COMPLETE SEED DATA DONE")
            print("=" * 60)
            print(f"  Tenant:              {tenant_id}")
            print(f"  Expenses:            +5 (if needed)")
            print(f"  Expense Reports:     3")
            print(f"  Risk Scores:         3")
            print(f"  Audit Trails:        3")
            print(f"  Notifications:       +5 (if needed)")
            print(f"  Expense Policies:    3")
            print(f"  Categories + GL:     10")
            print(f"  VAT Rules:           4")
            print(f"  Tax Declarations:    2")
            print(f"  Bank Transactions:   +10 (if needed)")
            print(f"  Financial Snapshots: 1")
            print("=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_v4_complete())
