"""Fix tax data: add sales entries with TVA collectee + fix computed_data."""
import asyncio, json, uuid, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://dou_user:dou_password123@localhost:5433/dou_expense_audit"

async def fix():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        r = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_id = str(r.scalar())
        r2 = await db.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = str(r2.scalar())

        # 1. Add sales journal entries with TVA collectee
        print("[1] Adding sales entries with TVA collectee...")
        sales = [
            ("VTE-2026-0001", date(2026, 1, 10), "Prestation consulting Alpha SAS", 5000, 20, 1, "706000", "411000", "445710"),
            ("VTE-2026-0002", date(2026, 1, 18), "Vente marchandises Beta EURL", 3000, 20, 1, "707000", "411000", "445710"),
            ("VTE-2026-0003", date(2026, 1, 25), "Prestation formation client", 1500, 10, 1, "706000", "411000", "445711"),
            ("VTE-2026-0004", date(2026, 2, 5), "Vente logiciel licence", 2500, 20, 2, "706000", "411000", "445710"),
            ("VTE-2026-0005", date(2026, 2, 15), "Mission conseil Mars", 4000, 20, 2, "706000", "411000", "445710"),
        ]

        for entry_num, entry_date, desc, ht, vat_rate, period, rev_acct, client_acct, tva_acct in sales:
            r = await db.execute(text("SELECT id FROM journal_entries WHERE entry_number = :n AND tenant_id = :t"),
                                 {"n": entry_num, "t": tenant_id})
            if r.scalar():
                print(f"  Skip: {entry_num}")
                continue

            vat = round(ht * vat_rate / 100, 2)
            ttc = ht + vat
            eid = str(uuid.uuid4())

            await db.execute(text(
                "INSERT INTO journal_entries (id, tenant_id, entry_number, journal_code, entry_date, description, "
                "status, source_type, fiscal_year, fiscal_period, total_debit, total_credit, is_balanced, created_by, created_at, updated_at) "
                "VALUES (:id, :tid, :enum, 'VTE', :edate, :desc, 'validated', 'invoice', 2026, :period, :ttc, :ttc, true, :uid, NOW(), NOW())"
            ), {"id": eid, "tid": tenant_id, "enum": entry_num, "edate": entry_date,
                "desc": desc, "period": period, "ttc": ttc, "uid": user_id})

            # Debit Client = TTC
            await db.execute(text(
                "INSERT INTO journal_entry_lines (id, entry_id, line_number, account_code, account_name, debit, credit, label, created_at) "
                "VALUES (:id, :eid, 1, :acct, 'Clients', :amt, 0, :label, NOW())"
            ), {"id": str(uuid.uuid4()), "eid": eid, "acct": client_acct, "amt": ttc, "label": desc})

            # Credit Revenue = HT
            await db.execute(text(
                "INSERT INTO journal_entry_lines (id, entry_id, line_number, account_code, account_name, debit, credit, label, created_at) "
                "VALUES (:id, :eid, 2, :acct, 'Produits', 0, :amt, :label, NOW())"
            ), {"id": str(uuid.uuid4()), "eid": eid, "acct": rev_acct, "amt": ht, "label": desc})

            # Credit TVA collectee = VAT
            await db.execute(text(
                "INSERT INTO journal_entry_lines (id, entry_id, line_number, account_code, account_name, debit, credit, label, vat_rate, vat_amount, created_at) "
                "VALUES (:id, :eid, 3, :acct, 'TVA collectee', 0, :amt, :label, :vr, :va, NOW())"
            ), {"id": str(uuid.uuid4()), "eid": eid, "acct": tva_acct, "amt": vat, "label": f"TVA {vat_rate}%", "vr": vat_rate, "va": vat})

            print(f"  Added: {entry_num} HT={ht} TVA={vat} TTC={ttc}")

        # 2. Fix declaration computed_data
        print("[2] Fixing declaration computed_data...")

        jan_data = json.dumps({
            "period_start": "2026-01-01", "period_end": "2026-01-31",
            "collected_vat_20": "1600.00", "collected_vat_10": "150.00",
            "collected_vat_55": "0", "collected_vat_21": "0",
            "total_collected": "1750.00",
            "base_20": "8000.00", "base_10": "1500.00",
            "base_55": "0", "base_21": "0",
            "deductible_vat_goods": "500.00",
            "deductible_vat_services": "500.00",
            "deductible_vat_immobilisations": "0",
            "total_deductible": "500.00",
            "vat_due": "1250.00", "credit_vat": "0",
            "net_amount": "1250.00",
        })
        await db.execute(text("UPDATE tax_declarations SET computed_data = :cd WHERE period_start = '2026-01-01'"),
                         {"cd": jan_data})

        feb_data = json.dumps({
            "period_start": "2026-02-01", "period_end": "2026-02-28",
            "collected_vat_20": "1300.00", "collected_vat_10": "0",
            "collected_vat_55": "0", "collected_vat_21": "0",
            "total_collected": "1300.00",
            "base_20": "6500.00", "base_10": "0",
            "base_55": "0", "base_21": "0",
            "deductible_vat_goods": "410.00",
            "deductible_vat_services": "410.00",
            "deductible_vat_immobilisations": "0",
            "total_deductible": "410.00",
            "vat_due": "890.00", "credit_vat": "0",
            "net_amount": "890.00",
        })
        await db.execute(text("UPDATE tax_declarations SET computed_data = :cd WHERE period_start = '2026-02-01'"),
                         {"cd": feb_data})

        print("  Updated Jan + Feb computed_data")

        await db.commit()
        print("[DONE] Tax data fixed!")

    await engine.dispose()

asyncio.run(fix())
