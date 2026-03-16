"""
Seed script for V4 tables with realistic French test data.
Populates: PCG accounts, fiscal periods, third parties, journal entries,
expenses, client dossiers, bank accounts/transactions, notifications,
tax calendar, invoices, and dossier timeline events.

Usage: python scripts/seed_v4_data.py
"""
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add parent directory to path so we can import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://dou_user:dou_password123@localhost:5433/dou_expense_audit"


def uid():
    """Generate a new UUID4."""
    return uuid.uuid4()


async def seed_v4():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # ------------------------------------------------------------------
            # Fetch tenant_id and user_id
            # ------------------------------------------------------------------
            print("[1/12] Fetching tenant and admin user...")
            row = (await db.execute(text("SELECT id FROM tenants LIMIT 1"))).fetchone()
            if not row:
                print("ERROR: No tenant found. Run the base seed_data.py first.")
                return
            tenant_id = row[0]
            print(f"  Tenant ID: {tenant_id}")

            row = (await db.execute(text(
                "SELECT id FROM users WHERE email = 'admin@doucompta.fr'"
            ))).fetchone()
            if not row:
                # Fallback to any admin user
                row = (await db.execute(text("SELECT id FROM users LIMIT 1"))).fetchone()
            if not row:
                print("ERROR: No user found. Run the base seed_data.py first.")
                return
            user_id = row[0]
            print(f"  User  ID: {user_id}")

            # ==================================================================
            # 1. PCG Accounts
            # ==================================================================
            print("[2/12] Seeding PCG accounts...")
            from services.accounting_service.pcg_seed import get_pcg_seed_data
            pcg_data = get_pcg_seed_data()
            pcg_count = 0
            for acct in pcg_data:
                acct_id = uid()
                await db.execute(text("""
                    INSERT INTO pcg_accounts
                        (id, tenant_id, account_code, account_name, account_class,
                         account_type, parent_code, is_system, is_active, created_at, updated_at)
                    VALUES
                        (:id, :tid, :code, :name, :cls, :atype, :parent, true, true, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": acct_id, "tid": tenant_id,
                    "code": acct["account_code"], "name": acct["account_name"],
                    "cls": acct["account_class"], "atype": acct["account_type"],
                    "parent": acct.get("parent_code"),
                })
                pcg_count += 1
            print(f"  Inserted/skipped {pcg_count} PCG accounts.")

            # ==================================================================
            # 2. Fiscal Periods (2025 + 2026)
            # ==================================================================
            print("[3/12] Seeding fiscal periods...")
            fp_count = 0
            for year in (2025, 2026):
                for month in range(1, 13):
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    fp_id = uid()
                    await db.execute(text("""
                        INSERT INTO fiscal_periods
                            (id, tenant_id, fiscal_year, period_number,
                             start_date, end_date, status, created_at, updated_at)
                        VALUES
                            (:id, :tid, :yr, :pn, :sd, :ed, 'open', NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": fp_id, "tid": tenant_id,
                        "yr": year, "pn": month,
                        "sd": date(year, month, 1),
                        "ed": date(year, month, last_day),
                    })
                    fp_count += 1
            print(f"  Inserted/skipped {fp_count} fiscal periods.")

            # ==================================================================
            # 3. Third Parties
            # ==================================================================
            print("[4/12] Seeding third parties...")
            third_parties = [
                # (name, type, siren, vat_number, default_account)
                ("Fournitures Martin SARL", "supplier", "312456789", "FR32312456789", "401100"),
                ("Restaurant Le Petit Bistrot", "supplier", "423567890", "FR42423567890", "401200"),
                ("Hotel Mercure Paris", "supplier", "534678901", "FR53534678901", "401200"),
                ("SFR Telecom", "supplier", "645789012", "FR64645789012", "401100"),
                ("Cabinet Dupont & Associes", "supplier", "756890123", "FR75756890123", "401200"),
                ("Client Alpha SAS", "customer", "867901234", "FR86867901234", "411000"),
                ("Client Beta EURL", "customer", "978012345", "FR97978012345", "411000"),
                ("Jean Dupont", "employee", None, None, "421000"),
            ]
            tp_ids = {}
            for tp_name, tp_type, tp_siren, tp_vat, tp_acct in third_parties:
                tp_id = uid()
                tp_ids[tp_name] = tp_id
                await db.execute(text("""
                    INSERT INTO third_parties
                        (id, tenant_id, type, name, siren, vat_number,
                         default_account_code, is_active, created_at, updated_at)
                    VALUES
                        (:id, :tid, :tp, :nm, :sr, :vn, :da, true, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": tp_id, "tid": tenant_id,
                    "tp": tp_type, "nm": tp_name,
                    "sr": tp_siren, "vn": tp_vat, "da": tp_acct,
                })
            print(f"  Inserted/skipped {len(third_parties)} third parties.")

            # ==================================================================
            # 4. Journal Entries (10 entries in ACH journal)
            # ==================================================================
            print("[5/12] Seeding journal entries...")

            # Each entry: (description, entry_date, expense_account, ht_amount, tva_rate, supplier_name)
            journal_entries_data = [
                ("Repas affaires - Le Petit Bistrot",     date(2026, 1, 15), "625700", Decimal("45.50"),  Decimal("10.00"), "Restaurant Le Petit Bistrot"),
                ("Fournitures de bureau",                  date(2026, 1, 20), "606400", Decimal("125.00"), Decimal("20.00"), "Fournitures Martin SARL"),
                ("Billet de train Paris-Lyon",             date(2026, 1, 25), "625100", Decimal("89.00"),  Decimal("10.00"), "SFR Telecom"),
                ("Nuit hotel Paris - deplacement",         date(2026, 2, 3),  "625600", Decimal("185.00"), Decimal("10.00"), "Hotel Mercure Paris"),
                ("Facture telephonie mobile",              date(2026, 2, 10), "626000", Decimal("59.99"),  Decimal("20.00"), "SFR Telecom"),
                ("Honoraires conseil juridique",           date(2026, 2, 15), "622600", Decimal("2400.00"),Decimal("20.00"), "Cabinet Dupont & Associes"),
                ("Loyer bureaux - fevrier 2026",           date(2026, 2, 28), "613200", Decimal("1500.00"),Decimal("20.00"), "Fournitures Martin SARL"),
                ("Prime assurance RC pro",                 date(2026, 3, 1),  "616000", Decimal("350.00"), Decimal("0.00"),  "Cabinet Dupont & Associes"),
                ("Dejeuner client - prospection",          date(2026, 3, 5),  "625700", Decimal("78.50"),  Decimal("10.00"), "Restaurant Le Petit Bistrot"),
                ("Abonnement logiciel comptable",          date(2026, 3, 10), "628000", Decimal("49.99"),  Decimal("20.00"), "Fournitures Martin SARL"),
            ]

            je_ids = []
            for idx, (desc, entry_date, expense_acct, ht_amount, tva_rate, supplier) in enumerate(journal_entries_data, start=1):
                je_id = uid()
                je_ids.append(je_id)
                supplier_id = tp_ids.get(supplier)

                # Compute TVA
                if tva_rate > 0:
                    tva_amount = (ht_amount * tva_rate / Decimal("100")).quantize(Decimal("0.01"))
                else:
                    tva_amount = Decimal("0.00")
                ttc = ht_amount + tva_amount

                entry_number = f"ACH-2026-{idx:04d}"
                fiscal_period = entry_date.month

                # Insert journal entry
                await db.execute(text("""
                    INSERT INTO journal_entries
                        (id, tenant_id, entry_number, journal_code, entry_date,
                         description, status, fiscal_year, fiscal_period,
                         total_debit, total_credit, is_balanced,
                         created_by, created_at, updated_at)
                    VALUES
                        (:id, :tid, :en, 'ACH', :ed, :desc, 'validated',
                         :fy, :fp, :td, :tc, true, :uid, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": je_id, "tid": tenant_id,
                    "en": entry_number, "ed": entry_date,
                    "desc": desc, "fy": entry_date.year, "fp": fiscal_period,
                    "td": ttc, "tc": ttc, "uid": user_id,
                })

                # Line 1: Expense debit (HT)
                await db.execute(text("""
                    INSERT INTO journal_entry_lines
                        (id, entry_id, line_number, account_code, account_name,
                         debit, credit, label, currency, created_at)
                    VALUES
                        (:id, :eid, 1, :acct, :aname, :debit, 0, :lbl, 'EUR', NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": uid(), "eid": je_id,
                    "acct": expense_acct, "aname": desc,
                    "debit": ht_amount, "lbl": desc,
                })

                line_num = 2
                # Line 2: TVA debit (if applicable)
                if tva_rate > 0:
                    await db.execute(text("""
                        INSERT INTO journal_entry_lines
                            (id, entry_id, line_number, account_code, account_name,
                             debit, credit, label, vat_rate, vat_amount, currency, created_at)
                        VALUES
                            (:id, :eid, :ln, '445660', 'TVA deductible sur ABS',
                             :debit, 0, :lbl, :vr, :va, 'EUR', NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "eid": je_id, "ln": line_num,
                        "debit": tva_amount, "lbl": f"TVA {tva_rate}% - {desc}",
                        "vr": tva_rate, "va": tva_amount,
                    })
                    line_num += 1

                # Line 3 (or 2): Supplier credit (TTC)
                await db.execute(text("""
                    INSERT INTO journal_entry_lines
                        (id, entry_id, line_number, account_code, account_name,
                         debit, credit, label, third_party_id, currency, created_at)
                    VALUES
                        (:id, :eid, :ln, '401000', 'Fournisseurs',
                         0, :credit, :lbl, :tpid, 'EUR', NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": uid(), "eid": je_id, "ln": line_num,
                    "credit": ttc, "lbl": supplier,
                    "tpid": supplier_id,
                })

            print(f"  Inserted/skipped {len(journal_entries_data)} journal entries with lines.")

            # ==================================================================
            # 5. Expenses (5 sample expenses)
            # ==================================================================
            print("[6/12] Seeding expenses...")
            expenses_data = [
                # (amount, expense_date, category, description, merchant, status, approval_status, vat_amount, vat_rate)
                (Decimal("45.50"),  date(2026, 1, 15), "meals",         "Repas affaires",            "Le Petit Bistrot",     "draft",     None,       Decimal("4.14"),  Decimal("10.00")),
                (Decimal("125.00"), date(2026, 1, 20), "office",        "Fournitures de bureau",     "Martin SARL",          "submitted", None,       Decimal("20.83"), Decimal("20.00")),
                (Decimal("185.00"), date(2026, 2, 3),  "accommodation", "Nuit hotel deplacement",    "Hotel Mercure Paris",  "approved",  "approved", Decimal("16.82"), Decimal("10.00")),
                (Decimal("89.00"),  date(2026, 1, 25), "transport",     "Train Paris-Lyon",          "SNCF",                 "approved",  "approved", Decimal("8.09"),  Decimal("10.00")),
                (Decimal("78.50"),  date(2026, 3, 5),  "meals",         "Dejeuner client",           "Le Petit Bistrot",     "rejected",  "rejected", Decimal("7.14"),  Decimal("10.00")),
            ]

            for amt, exp_date, cat, desc, merchant, status, appr_status, vat_amt, vat_r in expenses_data:
                exp_id = uid()
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
                    "id": exp_id, "tid": tenant_id, "uid": user_id,
                    "amt": amt, "ed": exp_date,
                    "cat": cat, "desc": desc, "merch": merchant,
                    "st": status, "ast": appr_status,
                    "va": vat_amt, "vr": vat_r,
                })
            print(f"  Inserted/skipped {len(expenses_data)} expenses.")

            # ==================================================================
            # 6. Client Dossiers (3 dossiers)
            # ==================================================================
            print("[7/12] Seeding client dossiers...")
            dossiers_data = [
                ("Boulangerie Dupont SARL", "123456789", "12345678900015", "SARL", "1071C",
                 "reel_normal", "12 Rue de la Paix", None, "75002", "Paris",
                 "01 42 33 44 55", "contact@boulangerie-dupont.fr"),
                ("Tech Solutions SAS", "987654321", "98765432100028", "SAS", "6201Z",
                 "reel_simplifie", "45 Avenue des Champs-Elysees", "Bat B", "75008", "Paris",
                 "01 56 78 90 12", "info@techsolutions.fr"),
                ("Cabinet Moreau", "456789123", "45678912300031", "Profession liberale", "6920Z",
                 "franchise", "8 Boulevard Haussmann", None, "75009", "Paris",
                 "01 48 78 12 34", "contact@cabinet-moreau.fr"),
            ]

            dossier_ids = []
            for (cname, siren, siret, legal, naf, regime,
                 addr1, addr2, postal, city, phone, email) in dossiers_data:
                d_id = uid()
                dossier_ids.append((d_id, cname))
                await db.execute(text("""
                    INSERT INTO client_dossiers
                        (id, tenant_id, client_name, siren, siret, legal_form,
                         naf_code, fiscal_year_start, fiscal_year_end,
                         regime_tva, accountant_id, status,
                         address_line1, address_line2, postal_code, city, country,
                         phone, email, created_at, updated_at)
                    VALUES
                        (:id, :tid, :cn, :sr, :st, :lf,
                         :naf, :fys, :fye,
                         :rt, :aid, 'active',
                         :a1, :a2, :pc, :ct, 'FR',
                         :ph, :em, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": d_id, "tid": tenant_id, "cn": cname,
                    "sr": siren, "st": siret, "lf": legal,
                    "naf": naf, "fys": date(2026, 1, 1), "fye": date(2026, 12, 31),
                    "rt": regime, "aid": user_id,
                    "a1": addr1, "a2": addr2, "pc": postal, "ct": city,
                    "ph": phone, "em": email,
                })
            print(f"  Inserted/skipped {len(dossiers_data)} client dossiers.")

            # ==================================================================
            # 7. Bank Accounts (2 accounts)
            # ==================================================================
            print("[8/12] Seeding bank accounts...")
            bnp_id = uid()
            sg_id = uid()
            await db.execute(text("""
                INSERT INTO bank_accounts
                    (id, tenant_id, account_name, iban, bic, bank_name,
                     currency, balance, balance_date, pcg_account_code,
                     connection_type, is_active, created_at, updated_at)
                VALUES
                    (:id, :tid, 'Compte courant BNP Paribas',
                     'FR7630004000031234567890143', 'BNPAFRPPXXX', 'BNP Paribas',
                     'EUR', 24350.67, :bd, '512000', 'manual', true, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {"id": bnp_id, "tid": tenant_id, "bd": date(2026, 3, 15)})

            await db.execute(text("""
                INSERT INTO bank_accounts
                    (id, tenant_id, account_name, iban, bic, bank_name,
                     currency, balance, balance_date, pcg_account_code,
                     connection_type, is_active, created_at, updated_at)
                VALUES
                    (:id, :tid, 'Compte epargne Societe Generale',
                     'FR7630003000401234567890185', 'SOGEFRPPXXX', 'Societe Generale',
                     'EUR', 50000.00, :bd, '512000', 'manual', true, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {"id": sg_id, "tid": tenant_id, "bd": date(2026, 3, 15)})
            print("  Inserted/skipped 2 bank accounts.")

            # ==================================================================
            # 8. Bank Transactions (10 for BNP account)
            # ==================================================================
            print("[9/12] Seeding bank transactions...")
            bank_txns = [
                # (date, amount, label, reference, counterparty, txn_type, category)
                (date(2026, 1, 5),   Decimal("-1500.00"), "LOYER JANVIER BUREAU 3EME",            "VIR-2026-001", "SCI IMMOBILIERE PARIS",  "virement",       "loyer"),
                (date(2026, 1, 10),  Decimal("8500.00"),  "VIREMENT CLIENT ALPHA SAS FAC-2025-12","VIR-2026-002", "Client Alpha SAS",       "virement",       "encaissement"),
                (date(2026, 1, 15),  Decimal("-45.50"),   "CB LE PETIT BISTROT PARIS",            "CB-2026-001",  "Le Petit Bistrot",       "carte_bancaire", "restauration"),
                (date(2026, 1, 20),  Decimal("-125.00"),  "CB FOURNITURES MARTIN PARIS",          "CB-2026-002",  "Fournitures Martin",     "carte_bancaire", "fournitures"),
                (date(2026, 1, 25),  Decimal("-89.00"),   "CB SNCF BILLET TGV INOUI",             "CB-2026-003",  "SNCF",                   "carte_bancaire", "transport"),
                (date(2026, 2, 1),   Decimal("-350.00"),  "PRELEVEMENT AXA ASSURANCE RC PRO",     "PRLV-2026-001","AXA France",             "prelevement",    "assurance"),
                (date(2026, 2, 3),   Decimal("-185.00"),  "CB HOTEL MERCURE PARIS GARE LYON",     "CB-2026-004",  "Hotel Mercure Paris",    "carte_bancaire", "hotel"),
                (date(2026, 2, 10),  Decimal("-59.99"),   "PRELEVEMENT SFR MOBILE PRO",           "PRLV-2026-002","SFR",                    "prelevement",    "telecom"),
                (date(2026, 2, 15),  Decimal("-2400.00"), "VIR CABINET DUPONT HONORAIRES FEV",    "VIR-2026-003", "Cabinet Dupont",         "virement",       "honoraires"),
                (date(2026, 2, 28),  Decimal("12750.00"), "VIREMENT CLIENT BETA EURL FAC-2026-01","VIR-2026-004", "Client Beta EURL",       "virement",       "encaissement"),
            ]
            for txn_date, amount, label, ref, counterparty, txn_type, cat in bank_txns:
                await db.execute(text("""
                    INSERT INTO bank_transactions
                        (id, bank_account_id, transaction_date, value_date, amount,
                         currency, label, reference, counterparty_name,
                         transaction_type, category, reconciliation_status,
                         created_at, updated_at)
                    VALUES
                        (:id, :baid, :td, :vd, :amt,
                         'EUR', :lbl, :ref, :cp,
                         :tt, :cat, 'unmatched',
                         NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": uid(), "baid": bnp_id,
                    "td": txn_date, "vd": txn_date,
                    "amt": amount, "lbl": label, "ref": ref,
                    "cp": counterparty, "tt": txn_type, "cat": cat,
                })
            print(f"  Inserted/skipped {len(bank_txns)} bank transactions.")

            # ==================================================================
            # 9. Notifications (5 for admin user)
            # ==================================================================
            print("[10/12] Seeding notifications...")
            notifications = [
                ("expense_approved", "Note de frais approuvee",
                 "Votre note de frais NF-2026-003 de 185.00 EUR a ete approuvee.",
                 "normal", "/expenses"),
                ("declaration_due", "Echeance TVA CA3 - Fevrier 2026",
                 "La declaration CA3 pour la periode de fevrier 2026 est a deposer avant le 24/03/2026.",
                 "high", "/tax/declarations"),
                ("anomaly_detected", "Anomalie detectee - Doublon potentiel",
                 "Un doublon potentiel a ete detecte : 2 notes de frais de 45.50 EUR au meme restaurant le 15/01/2026.",
                 "high", "/audit/anomalies"),
                ("entry_created", "Ecriture comptable creee",
                 "L'ecriture ACH-2026-0006 (Honoraires conseil juridique - 2400.00 EUR) a ete comptabilisee.",
                 "normal", "/accounting/entries"),
                ("document_received", "Document recu - Facture fournisseur",
                 "Une nouvelle facture de Fournitures Martin SARL (125.00 EUR TTC) a ete recue et indexee.",
                 "normal", "/documents"),
            ]
            for ntype, title, body, priority, action_url in notifications:
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
            print(f"  Inserted/skipped {len(notifications)} notifications.")

            # ==================================================================
            # 10. Tax Calendar (4 upcoming CA3 deadlines)
            # ==================================================================
            print("[11/12] Seeding tax calendar entries...")
            # Use the first dossier for tax calendar
            first_dossier_id = dossier_ids[0][0] if dossier_ids else None

            tax_deadlines = [
                # (declaration_type, due_date, period description)
                ("CA3", date(2026, 4, 24), "TVA CA3 - Mars 2026"),
                ("CA3", date(2026, 5, 24), "TVA CA3 - Avril 2026"),
                ("CA3", date(2026, 6, 24), "TVA CA3 - Mai 2026"),
                ("CA3", date(2026, 7, 24), "TVA CA3 - Juin 2026"),
            ]
            for decl_type, due, notes in tax_deadlines:
                await db.execute(text("""
                    INSERT INTO tax_calendar
                        (id, tenant_id, dossier_id, declaration_type,
                         due_date, status, reminder_sent, notes,
                         created_at, updated_at)
                    VALUES
                        (:id, :tid, :did, :dt,
                         :dd, 'upcoming', false, :nt,
                         NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": uid(), "tid": tenant_id,
                    "did": first_dossier_id, "dt": decl_type,
                    "dd": due, "nt": notes,
                })
            print(f"  Inserted/skipped {len(tax_deadlines)} tax calendar entries.")

            # ==================================================================
            # 11. Invoices (3 sample invoices with line items)
            # ==================================================================
            print("[12/12] Seeding invoices and dossier timeline...")

            invoices_data = [
                # (number, type, status, issuer_name, issuer_siren, recipient_name, recipient_siren,
                #  issue_date, due_date, total_ht, total_vat, total_ttc, lines)
                ("FAC-2026-0001", "sent", "sent",
                 "DouCompta SAS", "111222333", "Client Alpha SAS", "867901234",
                 date(2026, 1, 31), date(2026, 3, 2),
                 Decimal("5000.00"), Decimal("1000.00"), Decimal("6000.00"),
                 [
                     (1, "Mission de conseil comptable - Janvier 2026", Decimal("1"), Decimal("3000.0000"), Decimal("20.00"), Decimal("3000.00"), Decimal("600.00"), "706000"),
                     (2, "Formation equipe comptable (2 jours)", Decimal("1"), Decimal("2000.0000"), Decimal("20.00"), Decimal("2000.00"), Decimal("400.00"), "706000"),
                 ]),
                ("FAC-2026-0002", "sent", "paid",
                 "DouCompta SAS", "111222333", "Client Beta EURL", "978012345",
                 date(2026, 2, 15), date(2026, 3, 17),
                 Decimal("8500.00"), Decimal("1700.00"), Decimal("10200.00"),
                 [
                     (1, "Tenue comptable - T1 2026", Decimal("1"), Decimal("6000.0000"), Decimal("20.00"), Decimal("6000.00"), Decimal("1200.00"), "706000"),
                     (2, "Etablissement declarations fiscales", Decimal("1"), Decimal("2500.0000"), Decimal("20.00"), Decimal("2500.00"), Decimal("500.00"), "706000"),
                 ]),
                ("FACF-2026-0001", "received", "validated",
                 "Fournitures Martin SARL", "312456789", "DouCompta SAS", "111222333",
                 date(2026, 1, 20), date(2026, 2, 19),
                 Decimal("125.00"), Decimal("25.00"), Decimal("150.00"),
                 [
                     (1, "Ramettes papier A4 (10 unites)", Decimal("10"), Decimal("8.5000"), Decimal("20.00"), Decimal("85.00"), Decimal("17.00"), "606400"),
                     (2, "Cartouches encre imprimante", Decimal("2"), Decimal("20.0000"), Decimal("20.00"), Decimal("40.00"), Decimal("8.00"), "606400"),
                 ]),
            ]

            for (inv_num, inv_type, inv_status, issuer, issuer_sr, recip, recip_sr,
                 issue_dt, due_dt, total_ht, total_vat, total_ttc, lines) in invoices_data:
                inv_id = uid()
                dossier_ref = first_dossier_id  # link to first dossier
                await db.execute(text("""
                    INSERT INTO invoices
                        (id, tenant_id, dossier_id, invoice_number, type, format, status,
                         issuer_name, issuer_siren, recipient_name, recipient_siren,
                         issue_date, due_date,
                         total_ht, total_vat, total_ttc, currency,
                         created_at, updated_at)
                    VALUES
                        (:id, :tid, :did, :inum, :itp, 'facturx', :ist,
                         :iname, :isr, :rname, :rsr,
                         :idate, :ddate,
                         :tht, :tvat, :tttc, 'EUR',
                         NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "id": inv_id, "tid": tenant_id, "did": dossier_ref,
                    "inum": inv_num, "itp": inv_type, "ist": inv_status,
                    "iname": issuer, "isr": issuer_sr,
                    "rname": recip, "rsr": recip_sr,
                    "idate": issue_dt, "ddate": due_dt,
                    "tht": total_ht, "tvat": total_vat, "tttc": total_ttc,
                })

                for (ln, desc, qty, unit_price, vat_rate, line_ht, line_vat, acct_code) in lines:
                    await db.execute(text("""
                        INSERT INTO invoice_lines
                            (id, invoice_id, line_number, description,
                             quantity, unit_price, vat_rate,
                             line_total_ht, line_total_vat, account_code,
                             created_at)
                        VALUES
                            (:id, :iid, :ln, :desc,
                             :qty, :up, :vr,
                             :lht, :lvat, :ac,
                             NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "iid": inv_id, "ln": ln, "desc": desc,
                        "qty": qty, "up": unit_price, "vr": vat_rate,
                        "lht": line_ht, "lvat": line_vat, "ac": acct_code,
                    })

            print(f"  Inserted/skipped {len(invoices_data)} invoices with line items.")

            # ==================================================================
            # 12. Dossier Timeline events
            # ==================================================================
            timeline_events = {
                "Boulangerie Dupont SARL": [
                    ("dossier_created", "Dossier cree", "Creation du dossier client Boulangerie Dupont SARL"),
                    ("document_uploaded", "Kbis depose", "Extrait Kbis telecharge et ajoute au dossier"),
                    ("declaration_submitted", "CA3 Janvier soumise", "Declaration TVA CA3 de janvier 2026 transmise via EDI"),
                ],
                "Tech Solutions SAS": [
                    ("dossier_created", "Dossier cree", "Creation du dossier client Tech Solutions SAS"),
                    ("accounting_review", "Revision comptable", "Premiere revision des ecritures du trimestre T1 2026"),
                ],
                "Cabinet Moreau": [
                    ("dossier_created", "Dossier cree", "Creation du dossier client Cabinet Moreau"),
                    ("settings_updated", "Parametres mis a jour", "Regime TVA mis a jour: franchise en base de TVA"),
                ],
            }

            tl_count = 0
            for d_id, d_name in dossier_ids:
                events = timeline_events.get(d_name, [])
                for evt_type, title, desc in events:
                    await db.execute(text("""
                        INSERT INTO dossier_timeline
                            (id, dossier_id, event_type, title, description,
                             performed_by, created_at)
                        VALUES
                            (:id, :did, :et, :tl, :desc, :uid, NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uid(), "did": d_id,
                        "et": evt_type, "tl": title, "desc": desc,
                        "uid": user_id,
                    })
                    tl_count += 1
            print(f"  Inserted/skipped {tl_count} dossier timeline events.")

            # ------------------------------------------------------------------
            # Commit everything
            # ------------------------------------------------------------------
            await db.commit()
            print("")
            print("=" * 60)
            print("  V4 SEED DATA COMPLETE")
            print("=" * 60)
            print(f"  Tenant:            {tenant_id}")
            print(f"  PCG Accounts:      {pcg_count}")
            print(f"  Fiscal Periods:    {fp_count}")
            print(f"  Third Parties:     {len(third_parties)}")
            print(f"  Journal Entries:   {len(journal_entries_data)}")
            print(f"  Expenses:          {len(expenses_data)}")
            print(f"  Client Dossiers:   {len(dossiers_data)}")
            print(f"  Bank Accounts:     2")
            print(f"  Bank Transactions: {len(bank_txns)}")
            print(f"  Notifications:     {len(notifications)}")
            print(f"  Tax Calendar:      {len(tax_deadlines)}")
            print(f"  Invoices:          {len(invoices_data)}")
            print(f"  Timeline Events:   {tl_count}")
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
    asyncio.run(seed_v4())
