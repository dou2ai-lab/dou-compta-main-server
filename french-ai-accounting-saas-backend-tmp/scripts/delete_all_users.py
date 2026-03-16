"""
Delete all users from the database.
Handles foreign key order: clears user_roles and user-referencing rows, then deletes users.
Run from backend dir: python scripts/delete_all_users.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend root so we can import common
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
)
# asyncpg uses postgresql:// (no +asyncpg in connection string for asyncpg.connect)
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)


async def main():
    try:
        import asyncpg
    except ImportError:
        print("Install asyncpg: pip install asyncpg")
        return 1

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Break self-reference: users.manager_id -> users.id
        await conn.execute("UPDATE users SET manager_id = NULL")
        # Tables that reference users (delete or null FK in dependency order)
        await conn.execute("DELETE FROM user_roles")
        await conn.execute("DELETE FROM approval_steps")
        await conn.execute("DELETE FROM approval_workflows")
        await conn.execute("DELETE FROM email_notifications")
        await conn.execute("UPDATE policy_violations SET resolved_by = NULL")
        await conn.execute("UPDATE expense_report_items SET added_by = NULL")
        await conn.execute("UPDATE expenses SET approved_by = NULL")
        # expense_report_items links reports and expenses; expenses has submitted_by (user)
        await conn.execute("DELETE FROM expense_report_items")
        # receipt_documents references expenses
        try:
            await conn.execute("DELETE FROM receipt_documents")
        except Exception:
            pass
        await conn.execute("DELETE FROM expenses")
        await conn.execute("DELETE FROM expense_reports")
        # Optional: clear auth/security tables that reference users (if tables exist)
        for table in ["security_audit_logs", "failed_login_attempts", "user_sessions"]:
            try:
                await conn.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        # Finally delete all users
        result = await conn.execute("DELETE FROM users")
        # result is like "DELETE 5"
        count = result.split()[-1] if result else "0"
        print(f"Done. Removed all users from the database (deleted {count} user(s)).")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
