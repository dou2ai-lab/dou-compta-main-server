# -----------------------------------------------------------------------------
# File: seed_data.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Seed script to create initial data for development
# -----------------------------------------------------------------------------

"""
Seed script for development data
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.models import Base, Tenant, User, Role, Permission, RolePermission, UserRole
from common.roles import ROLE_ADMIN, ROLE_EMPLOYEE, ROLE_APPROVER, ROLE_FINANCE
from services.auth.utils import get_password_hash
from services.admin.models import ExpenseCategory, GLAccount
import uuid

# Register all models with Base.metadata so create_all creates every table (e.g. expense_policies for policy_violations FK)
import common.models  # noqa: F401
import services.admin.models  # noqa: F401
import services.file_service.models  # noqa: F401
import services.audit.models  # noqa: F401

_raw = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@postgres:5432/dou_expense_audit")
DATABASE_URL = _raw.replace("postgresql://", "postgresql+asyncpg://", 1) if _raw.startswith("postgresql://") else _raw

async def seed_data():
    """Seed initial data"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create tables if they don't exist (skip if BOOTSTRAP_SKIP_CREATE=1, e.g. after create_tables.py)
            if not os.getenv("BOOTSTRAP_SKIP_CREATE"):
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

            # Check if data already exists
            result = await db.execute(select(Tenant))
            existing_tenant = result.scalar_one_or_none()
            
            if existing_tenant:
                print("Data already seeded. Skipping...")
                return
            
            # Create default tenant
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Default Tenant",
                slug="default",
                status="active"
            )
            db.add(tenant)
            await db.flush()
            
            # Get or create permissions
            permissions_map = {}
            permission_names = [
                ("expense:create", "Create expenses", "expense", "create"),
                ("expense:read", "Read expenses", "expense", "read"),
                ("expense:update", "Update expenses", "expense", "update"),
                ("expense:delete", "Delete expenses", "expense", "delete"),
                ("expense:approve", "Approve expenses", "expense", "approve"),
                ("admin:read", "Read admin settings", "admin", "read"),
                ("admin:write", "Write admin settings", "admin", "write"),
                ("audit:read", "Read audit logs", "audit", "read"),
                ("audit:write", "Write audit logs", "audit", "write"),
                ("user:read", "Read users", "user", "read"),
                ("user:write", "Write users", "user", "write"),
            ]
            
            for name, desc, resource, action in permission_names:
                result = await db.execute(select(Permission).where(Permission.name == name))
                perm = result.scalar_one_or_none()
                if not perm:
                    perm = Permission(
                        name=name,
                        description=desc,
                        resource=resource,
                        action=action
                    )
                    db.add(perm)
                permissions_map[name] = perm
            
            await db.flush()
            
            # Create PRD roles: Admin, Employee, Approver, Finance
            admin_role = Role(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=ROLE_ADMIN,
                description="Administrator role (full access)",
                is_system_role=True
            )
            db.add(admin_role)
            await db.flush()

            employee_role = Role(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=ROLE_EMPLOYEE,
                description="Employee role (submit and manage own expenses)",
                is_system_role=True
            )
            db.add(employee_role)
            await db.flush()

            approver_role = Role(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=ROLE_APPROVER,
                description="Approver role (read and approve expenses)",
                is_system_role=True
            )
            db.add(approver_role)
            await db.flush()

            finance_role = Role(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name=ROLE_FINANCE,
                description="Finance role (approve, admin read, audit read)",
                is_system_role=True
            )
            db.add(finance_role)
            await db.flush()

            # Assign permissions to roles
            for perm in permissions_map.values():
                db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

            for perm_name in ["expense:create", "expense:read", "expense:update", "expense:delete"]:
                db.add(RolePermission(role_id=employee_role.id, permission_id=permissions_map[perm_name].id))

            db.add(RolePermission(role_id=approver_role.id, permission_id=permissions_map["expense:read"].id))
            db.add(RolePermission(role_id=approver_role.id, permission_id=permissions_map["expense:approve"].id))

            for perm_name in ["expense:read", "expense:approve", "admin:read", "audit:read"]:
                db.add(RolePermission(role_id=finance_role.id, permission_id=permissions_map[perm_name].id))

            await db.flush()

            # Create default users
            admin_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                password_hash=get_password_hash("password"),
                status="active"
            )
            db.add(admin_user)
            await db.flush()
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

            approver_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="approver@example.com",
                first_name="Approver",
                last_name="User",
                password_hash=get_password_hash("password"),
                status="active"
            )
            db.add(approver_user)
            await db.flush()
            db.add(UserRole(user_id=approver_user.id, role_id=approver_role.id))

            finance_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="finance@example.com",
                first_name="Finance",
                last_name="User",
                password_hash=get_password_hash("password"),
                status="active"
            )
            db.add(finance_user)
            await db.flush()
            db.add(UserRole(user_id=finance_user.id, role_id=finance_role.id))

            employee_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="user@example.com",
                first_name="Test",
                last_name="User",
                password_hash=get_password_hash("password"),
                status="active"
            )
            db.add(employee_user)
            await db.flush()
            db.add(UserRole(user_id=employee_user.id, role_id=employee_role.id))

            # Nancy admin user (for development / demo)
            nancy_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="gautamnancy324@gmail.com",
                first_name="Nancy",
                last_name="Gautam",
                password_hash=get_password_hash("Nancy@2323"),
                status="active"
            )
            db.add(nancy_user)
            await db.flush()
            db.add(UserRole(user_id=nancy_user.id, role_id=admin_role.id))

            # Default GL accounts (so Categories & GL dropdowns have options)
            default_gl_accounts = [
                ("6200", "Travel Expense", "expense"),
                ("6001", "Meals and catering", "expense"),
                ("6002", "Accommodation", "expense"),
                ("6003", "Transport and fuel", "expense"),
                ("6004", "Office supplies", "expense"),
                ("6005", "Training and education", "expense"),
                ("6006", "Professional services", "expense"),
                ("6010", "Other expenses", "expense"),
            ]
            gl_by_code = {}
            for code, account_name, acc_type in default_gl_accounts:
                gl = GLAccount(
                    tenant_id=tenant.id,
                    account_code=code,
                    account_name=account_name,
                    account_type=acc_type,
                    is_active=True,
                )
                db.add(gl)
                await db.flush()
                gl_by_code[code] = gl

            # Map category code -> GL account code for default mapping
            category_to_gl = {
                "meals": "6001", "travel": "6200", "accommodation": "6002", "transport": "6003",
                "office": "6004", "training": "6005", "professional": "6006",
                "client_gifts": "6010", "communications": "6010", "facilities": "6010",
            }
            # Default expense categories (name = display in UI, code = lowercase for policies/expense form)
            default_categories = [
                ("Meals", "meals", "Meals and food"),
                ("Travel", "travel", "Travel"),
                ("Accommodation", "accommodation", "Accommodation and lodging"),
                ("Transport", "transport", "Transport, taxi, fuel, parking"),
                ("Office", "office", "Office supplies and equipment"),
                ("Training", "training", "Training and education"),
                ("Client gifts", "client_gifts", "Client gifts and donations"),
                ("Communications", "communications", "Communications and telecom"),
                ("Professional", "professional", "Professional services"),
                ("Facilities", "facilities", "Facilities and maintenance"),
            ]
            travel_cat = None
            for display_name, code, desc in default_categories:
                gl_code = category_to_gl.get(code, "6010")
                gl_acc = gl_by_code.get(gl_code)
                cat = ExpenseCategory(
                    tenant_id=tenant.id,
                    name=display_name,
                    code=code,
                    description=desc,
                    is_active=True,
                    gl_account_id=gl_acc.id if gl_acc else None,
                )
                if code == "travel":
                    travel_cat = cat
                db.add(cat)
                await db.flush()

            # Business Travel as subcategory of Travel, mapped to 6200 – Travel Expense
            if travel_cat and gl_by_code.get("6200"):
                business_travel = ExpenseCategory(
                    tenant_id=tenant.id,
                    name="Business Travel",
                    code="business_travel",
                    description="Business travel expenses",
                    is_active=True,
                    parent_id=travel_cat.id,
                    gl_account_id=gl_by_code["6200"].id,
                )
                db.add(business_travel)

            await db.commit()

            print("✅ Seed data created successfully!")
            print("\nPRD roles: admin, employee, approver, finance")
            print("Default users created:")
            print("  - admin@example.com / password (Admin)")
            print("  - approver@example.com / password (Approver)")
            print("  - finance@example.com / password (Finance)")
            print("  - user@example.com / password (Employee)")
            print("  - gautamnancy324@gmail.com / Nancy@2323 (Admin)")
            print("\nDefault expense categories: meals, travel, accommodation, transport, office, training, client_gifts, communications, professional, facilities")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding data: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())


