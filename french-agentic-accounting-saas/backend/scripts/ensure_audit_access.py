# -----------------------------------------------------------------------------
# Ensure audit:read and audit:write permissions exist and are assigned to
# all Admin roles so users with Admin role get "Audit access required" resolved.
# Usage (from project root):
#   $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
#   python backend/scripts/ensure_audit_access.py
# -----------------------------------------------------------------------------
import asyncio
import os
import sys
import uuid
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

if (backend_root / ".env").exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(backend_root / ".env", override=True)
    except ImportError:
        pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from common.models import Permission, Role, RolePermission


async def ensure_audit_access() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        # 1) Ensure audit permissions exist (global Permission table)
        for name, desc, resource, action in [
            ("audit:read", "Read audit logs", "audit", "read"),
            ("audit:write", "Write audit logs", "audit", "write"),
        ]:
            r = await db.execute(select(Permission).where(Permission.name == name))
            perm = r.scalar_one_or_none()
            if not perm:
                perm = Permission(
                    id=uuid.uuid4(),
                    name=name,
                    description=desc,
                    resource=resource,
                    action=action,
                )
                db.add(perm)
                await db.flush()
                print(f"Created permission: {name}")
            else:
                print(f"Permission exists: {name}")

        # 2) Get audit permission ids
        r = await db.execute(select(Permission).where(Permission.name.in_(["audit:read", "audit:write"])))
        audit_perms = list(r.scalars().all())
        if not audit_perms:
            print("No audit permissions found.")
            return

        # 3) For every Admin role (any tenant), ensure it has audit:read and audit:write
        r = await db.execute(
            select(Role).where(Role.name == "admin", Role.deleted_at.is_(None))
        )
        admin_roles = r.scalars().all()
        if not admin_roles:
            print("No Admin roles found. Run seed_data/seed_roles or grant_admin_to_user first.")
            return

        added = 0
        for role in admin_roles:
            for perm in audit_perms:
                r2 = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if r2.scalar_one_or_none() is None:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
                    added += 1
                    print(f"Assigned {perm.name} to Admin role (tenant {role.tenant_id})")
        await db.flush()
        await db.commit()
        print(f"Done. New role-permission links added: {added}. Admin users should have audit access (log out and log in if needed).")


if __name__ == "__main__":
    asyncio.run(ensure_audit_access())
