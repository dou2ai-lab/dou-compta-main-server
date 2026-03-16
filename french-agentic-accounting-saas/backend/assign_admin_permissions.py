"""
Script to create and assign admin permissions to the Admin role
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys

# Import models
sys.path.append('/app/backend')
from common.models import User, Role, Permission, RolePermission, Tenant

# Database connection
DATABASE_URL = "postgresql+asyncpg://dou_user:dou_password@postgres:5432/dou_expense_audit"

async def assign_admin_permissions():
    """Create admin permissions and assign to Admin role"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Find user by email to get tenant
            email = "gautamnancy324@gmail.com"
            print(f"\n🔍 Looking for user with email: {email}")
            
            result = await session.execute(
                select(User).where(User.email == email, User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User not found with email: {email}")
                return
            
            print(f"✅ Found user: {user.first_name} {user.last_name}")
            print(f"   Tenant ID: {user.tenant_id}")
            
            # Find Admin role (PRD role name is lowercase: admin)
            print(f"\n🔍 Looking for Admin role...")
            role_result = await session.execute(
                select(Role).where(
                    Role.tenant_id == user.tenant_id,
                    Role.name == "admin",
                    Role.deleted_at.is_(None)
                )
            )
            admin_role = role_result.scalar_one_or_none()

            if not admin_role:
                print("❌ Admin role not found")
                return

            print(f"✅ Found Admin role (ID: {admin_role.id})")
            
            # Create or get admin permissions
            import uuid
            permissions_to_create = [
                {
                    "name": "admin:read",
                    "description": "Read access to admin panel",
                    "resource": "admin",
                    "action": "read"
                },
                {
                    "name": "admin:write",
                    "description": "Write access to admin panel",
                    "resource": "admin",
                    "action": "write"
                },
                {
                    "name": "user:read",
                    "description": "Read access to users",
                    "resource": "user",
                    "action": "read"
                },
                {
                    "name": "user:write",
                    "description": "Write access to users",
                    "resource": "user",
                    "action": "write"
                },
                {
                    "name": "expense:read",
                    "description": "Read access to expenses",
                    "resource": "expense",
                    "action": "read"
                },
                {
                    "name": "expense:write",
                    "description": "Write access to expenses",
                    "resource": "expense",
                    "action": "write"
                },
                {
                    "name": "policy:read",
                    "description": "Read access to policies",
                    "resource": "policy",
                    "action": "read"
                },
                {
                    "name": "policy:write",
                    "description": "Write access to policies",
                    "resource": "policy",
                    "action": "write"
                }
            ]
            
            created_permissions = []
            
            for perm_data in permissions_to_create:
                print(f"\n🔍 Checking permission: {perm_data['name']}")
                
                # Check if permission already exists
                perm_result = await session.execute(
                    select(Permission).where(Permission.name == perm_data["name"])
                )
                permission = perm_result.scalar_one_or_none()
                
                if not permission:
                    print(f"📝 Creating permission: {perm_data['name']}")
                    permission = Permission(
                        id=uuid.uuid4(),
                        name=perm_data["name"],
                        description=perm_data["description"],
                        resource=perm_data["resource"],
                        action=perm_data["action"]
                    )
                    session.add(permission)
                    await session.flush()
                    print(f"✅ Permission created (ID: {permission.id})")
                else:
                    print(f"✅ Permission already exists (ID: {permission.id})")
                
                created_permissions.append(permission)
            
            # Assign all permissions to Admin role
            print(f"\n📝 Assigning permissions to Admin role...")
            assigned_count = 0
            
            for permission in created_permissions:
                # Check if role already has this permission
                rp_result = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == admin_role.id,
                        RolePermission.permission_id == permission.id
                    )
                )
                existing_rp = rp_result.scalar_one_or_none()
                
                if not existing_rp:
                    role_permission = RolePermission(
                        role_id=admin_role.id,
                        permission_id=permission.id
                    )
                    session.add(role_permission)
                    assigned_count += 1
                    print(f"   ✅ Assigned: {permission.name}")
                else:
                    print(f"   ⏭️  Already assigned: {permission.name}")
            
            await session.flush()
            await session.commit()
            
            print(f"\n🎉 SUCCESS!")
            print(f"   Total permissions created/verified: {len(created_permissions)}")
            print(f"   New permissions assigned to Admin role: {assigned_count}")
            print(f"\n✅ User {email} can now access the Admin panel!")
            print(f"   Please log out and log in again to refresh your permissions.")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(assign_admin_permissions())

