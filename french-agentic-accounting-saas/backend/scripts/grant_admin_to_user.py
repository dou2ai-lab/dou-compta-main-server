# -----------------------------------------------------------------------------
# Grant Admin role to an existing user by email.
# Usage (from project root, DB on localhost:5433):
#   $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
#   python backend/scripts/grant_admin_to_user.py test5@gmail.com
# Or: python backend/scripts/grant_admin_to_user.py
#     (prompts for email or uses GRANT_ADMIN_EMAIL env)
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

from common.models import User, Role, UserRole, Permission, RolePermission


async def grant_admin(email: str) -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email.strip(), User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {email}")
            return
        # Find admin role (lowercase as in seed_roles / common.roles)
        result = await db.execute(
            select(Role).where(
                Role.tenant_id == user.tenant_id,
                Role.name == "admin",
                Role.deleted_at.is_(None),
            )
        )
        admin_role = result.scalar_one_or_none()
        if not admin_role:
            # Create admin role for this tenant and assign all permissions
            all_perms = (await db.execute(select(Permission))).scalars().all()
            if not all_perms:
                print("No permissions in DB. Run seed_data.py and seed_roles.py first.")
                return
            admin_role = Role(
                id=uuid.uuid4(),
                tenant_id=user.tenant_id,
                name="admin",
                description="Administrator role",
                is_system_role=True,
            )
            db.add(admin_role)
            await db.flush()
            for perm in all_perms:
                db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
            await db.flush()
            print("Created Admin role for tenant and assigned all permissions.")
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == admin_role.id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User {email} already has the Admin role.")
            return
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))
        await db.commit()
        print(f"Admin role granted to {email}. They may need to log out and log in again.")


if __name__ == "__main__":
    email = (sys.argv[1] if len(sys.argv) > 1 else os.getenv("GRANT_ADMIN_EMAIL", "")).strip()
    if not email:
        email = input("Enter user email: ").strip()
    if not email:
        print("Usage: python grant_admin_to_user.py <email>")
        sys.exit(1)
    asyncio.run(grant_admin(email))
