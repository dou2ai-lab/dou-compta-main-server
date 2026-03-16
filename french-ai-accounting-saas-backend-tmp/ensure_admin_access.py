"""
Script to ensure admin user has all permissions including audit access
Run this to grant full access to admin@example.com
"""
import asyncio
import asyncpg
import sys

async def ensure_admin_access():
    """Ensure admin user has all permissions"""
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user='dou_user',
        password='dou_password',
        database='dou_expense_audit'
    )
    
    try:
        print("🔍 Checking admin user and permissions...")
        
        # Get admin user
        admin_user = await conn.fetchrow(
            "SELECT id, email, tenant_id FROM users WHERE email = $1 AND deleted_at IS NULL",
            'admin@example.com'
        )
        
        if not admin_user:
            print("❌ Admin user not found. Creating admin user...")
            import bcrypt
            import uuid
            password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()
            
            # Get or create tenant
            tenant = await conn.fetchrow("SELECT id FROM tenants LIMIT 1")
            if not tenant:
                tenant_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO tenants (id, name, slug, status, created_at, updated_at)
                    VALUES ($1, 'Default Tenant', 'default', 'active', NOW(), NOW())
                """, tenant_id)
            else:
                tenant_id = tenant['id']
            
            admin_user_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
                VALUES ($1, $2, 'admin@example.com', 'Admin', 'User', $3, 'active', NOW(), NOW())
            """, admin_user_id, tenant_id, password_hash)
            admin_user = {'id': admin_user_id, 'email': 'admin@example.com', 'tenant_id': tenant_id}
            print("✅ Admin user created")
        else:
            print(f"✅ Found admin user: {admin_user['email']}")
        
        # Get admin role
        admin_role = await conn.fetchrow(
            "SELECT id FROM roles WHERE name = 'admin' AND tenant_id = $1 AND deleted_at IS NULL",
            admin_user['tenant_id']
        )
        
        if not admin_role:
            print("❌ Admin role not found. Creating admin role...")
            import uuid
            admin_role_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
                VALUES ($1, $2, 'admin', 'Administrator role', true, NOW(), NOW())
            """, admin_role_id, admin_user['tenant_id'])
            admin_role = {'id': admin_role_id}
            print("✅ Admin role created")
        else:
            print(f"✅ Found admin role (ID: {admin_role['id']})")
        
        # Ensure user has admin role
        user_role = await conn.fetchrow(
            "SELECT * FROM user_roles WHERE user_id = $1 AND role_id = $2",
            admin_user['id'], admin_role['id']
        )
        
        if not user_role:
            print("📝 Assigning admin role to user...")
            await conn.execute("""
                INSERT INTO user_roles (user_id, role_id, assigned_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT DO NOTHING
            """, admin_user['id'], admin_role['id'])
            print("✅ Admin role assigned to user")
        else:
            print("✅ User already has admin role")
        
        # Get all permissions
        all_permissions = await conn.fetch("""
            SELECT id, name FROM permissions
        """)
        
        if not all_permissions:
            print("📝 Creating all permissions...")
            import uuid
            permissions_to_create = [
                ('expense:create', 'Create expenses', 'expense', 'create'),
                ('expense:read', 'Read expenses', 'expense', 'read'),
                ('expense:update', 'Update expenses', 'expense', 'update'),
                ('expense:delete', 'Delete expenses', 'expense', 'delete'),
                ('expense:approve', 'Approve expenses', 'expense', 'approve'),
                ('admin:read', 'Read admin settings', 'admin', 'read'),
                ('admin:write', 'Write admin settings', 'admin', 'write'),
                ('audit:read', 'Read audit logs', 'audit', 'read'),
                ('audit:write', 'Write audit logs', 'audit', 'write'),
                ('user:read', 'Read users', 'user', 'read'),
                ('user:write', 'Write users', 'user', 'write'),
            ]
            
            for name, desc, resource, action in permissions_to_create:
                perm_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO permissions (id, name, description, resource, action, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (name) DO NOTHING
                """, perm_id, name, desc, resource, action)
            
            all_permissions = await conn.fetch("SELECT id, name FROM permissions")
            print(f"✅ Created {len(all_permissions)} permissions")
        
        # Assign ALL permissions to admin role
        print("📝 Assigning all permissions to admin role...")
        assigned_count = 0
        for perm in all_permissions:
            result = await conn.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, admin_role['id'], perm['id'])
            if '1' in str(result):
                assigned_count += 1
        
        print(f"✅ Assigned {assigned_count} permissions to admin role")
        print(f"   Total permissions available: {len(all_permissions)}")
        
        # Verify audit permission
        audit_permission = await conn.fetchrow("""
            SELECT rp.* FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = $1 AND p.name = 'audit:read'
        """, admin_role['id'])
        
        if audit_permission:
            print("✅ Audit permission (audit:read) is assigned to admin role")
        else:
            print("⚠️  Warning: Audit permission not found, but all permissions should be assigned")
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Admin user is now configured with full access")
        print("="*60)
        print("\n📧 Login Credentials:")
        print("   Email: admin@example.com")
        print("   Password: password")
        print("\n✅ This user has access to:")
        print("   - All expenses (create, read, update, delete, approve)")
        print("   - Admin panel (read, write)")
        print("   - Audit logs (read, write)")
        print("   - User management (read, write)")
        print("\n💡 Please log out and log in again to refresh permissions.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(ensure_admin_access())

