# -----------------------------------------------------------------------------
# File: seed_roles.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: Seed script to create Employee, Approver, and Finance roles
# -----------------------------------------------------------------------------

"""
Seed script for PRD roles: Admin, Employee, Approver, Finance.

Run from host (requires Postgres to accept host connections):
  After starting postgres, run: infrastructure\\fix-pg-trust.ps1  (so localhost:5433 uses trust)
  Then: python backend/scripts/seed_roles.py

Run from Docker (recommended if host auth fails):
  From project root: .\\infrastructure\\seed-roles.ps1
  Or: docker compose -f infrastructure/docker-compose.yml run --rm -e SEED_DATABASE_URL=postgresql+asyncpg://dou_user:dou_password123@postgres:5432/dou_expense_audit auth python scripts/seed_roles.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path (resolve to absolute so .env is found when run from any cwd)
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

# Load .env for other vars (e.g. JWT_SECRET); we do not use .env DATABASE_URL for this script
# so we always connect with the same credentials as infrastructure/docker-compose.yml
_env_path = backend_root / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=True)
    except ImportError:
        with open(_env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    val = value.strip().strip('"').strip("'").split("#")[0].strip()
                    os.environ[key.strip()] = val

# Always use URL that matches infrastructure/docker-compose.yml (ignore .env DATABASE_URL to avoid auth failures)
_DOCKER_DEFAULT = "postgresql+asyncpg://dou_user:dou_password123@127.0.0.1:5433/dou_expense_audit"
DATABASE_URL = (os.getenv("SEED_DATABASE_URL") or _DOCKER_DEFAULT).strip()
if not DATABASE_URL.startswith("postgresql+asyncpg://") and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.models import Tenant, Role, Permission, RolePermission
from common.roles import ROLE_ADMIN, ROLE_EMPLOYEE, ROLE_APPROVER, ROLE_FINANCE, PRD_ROLES
import uuid

async def seed_roles():
    """Seed PRD roles: Admin, Employee, Approver, Finance"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        try:
            # Get all tenants
            result = await db.execute(select(Tenant).where(Tenant.deleted_at.is_(None)))
            tenants = result.scalars().all()

            if not tenants:
                print("⚠️  No tenants found. Please run seed_data.py first to create a tenant.")
                return

            # Get all permissions
            result = await db.execute(select(Permission))
            all_permissions = result.scalars().all()
            permissions_map = {perm.name: perm for perm in all_permissions}

            if not permissions_map:
                print("⚠️  No permissions found. Please run seed_data.py first to create permissions.")
                return

            # Define role permissions (admin gets all via list of all permission names)
            all_perm_names = list(permissions_map.keys())
            role_permissions_map = {
                ROLE_ADMIN: all_perm_names,
                ROLE_EMPLOYEE: [
                    "expense:create",
                    "expense:read",
                    "expense:update",
                    "expense:delete",
                ],
                ROLE_APPROVER: [
                    "expense:read",
                    "expense:approve",
                ],
                ROLE_FINANCE: [
                    "expense:read",
                    "expense:approve",
                    "admin:read",
                    "audit:read",
                ],
            }

            for tenant in tenants:
                print(f"\n📋 Processing tenant: {tenant.name} ({tenant.slug})")

                # Check if PRD roles already exist
                result = await db.execute(
                    select(Role).where(
                        Role.tenant_id == tenant.id,
                        Role.name.in_(PRD_ROLES),
                        Role.deleted_at.is_(None)
                    )
                )
                existing_roles = {r.name: r for r in result.scalars().all()}

                # Create or update roles
                for role_name, permission_names in role_permissions_map.items():
                    if role_name in existing_roles:
                        role = existing_roles[role_name]
                        print(f"  ✓ Role '{role_name}' already exists, updating permissions...")
                    else:
                        role = Role(
                            id=uuid.uuid4(),
                            tenant_id=tenant.id,
                            name=role_name,
                            description=f"{role_name.capitalize()} role for expense management",
                            is_system_role=True
                        )
                        db.add(role)
                        await db.flush()
                        print(f"  ✓ Created role '{role_name}'")

                    # Remove existing role permissions
                    result = await db.execute(
                        select(RolePermission).where(RolePermission.role_id == role.id)
                    )
                    existing_rps = result.scalars().all()
                    for rp in existing_rps:
                        await db.delete(rp)

                    # Add new permissions
                    for perm_name in permission_names:
                        if perm_name in permissions_map:
                            perm = permissions_map[perm_name]
                            # Check if already exists
                            result = await db.execute(
                                select(RolePermission).where(
                                    RolePermission.role_id == role.id,
                                    RolePermission.permission_id == perm.id
                                )
                            )
                            existing_rp = result.scalar_one_or_none()
                            if not existing_rp:
                                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                                db.add(rp)
                                print(f"    - Added permission: {perm_name}")
                        else:
                            print(f"    ⚠️  Permission '{perm_name}' not found, skipping...")

                await db.flush()

            await db.commit()

            print("\n✅ Roles seeded successfully!")
            print("\nPRD roles created/updated:")
            print("  - admin: Full access (all permissions)")
            print("  - employee: Create, read, update, delete expenses")
            print("  - approver: Read and approve expenses")
            print("  - finance: Read, approve, admin read, audit read")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding roles: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_roles())
