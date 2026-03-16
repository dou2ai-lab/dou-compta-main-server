# Simple seed script using direct SQL
import asyncio
import asyncpg
import bcrypt
import uuid

async def seed_data():
    """Seed initial data using direct SQL"""
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user='dou_user',
        password='dou_password',
        database='dou_expense_audit'
    )
    
    try:
        # Enable UUID extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        
        # Check if tenant exists
        tenant_check = await conn.fetchval("SELECT id FROM tenants LIMIT 1")
        if tenant_check:
            print("Data already seeded. Skipping...")
            return
        
        # Hash password
        password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()
        
        # Create tenant
        tenant_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO tenants (id, name, slug, status, created_at, updated_at)
            VALUES ($1, 'Default Tenant', 'default', 'active', NOW(), NOW())
        """, tenant_id)
        
        # Create permissions
        permissions = {}
        perm_data = [
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
        
        for name, desc, resource, action in perm_data:
            perm_id = str(uuid.uuid4())
            existing = await conn.fetchval("SELECT id FROM permissions WHERE name = $1", name)
            if not existing:
                await conn.execute("""
                    INSERT INTO permissions (id, name, description, resource, action, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                """, perm_id, name, desc, resource, action)
            else:
                perm_id = str(existing)
            permissions[name] = perm_id
        
        # Create roles
        admin_role_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
            VALUES ($1, $2, 'admin', 'Administrator role', true, NOW(), NOW())
        """, admin_role_id, tenant_id)
        
        approver_role_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
            VALUES ($1, $2, 'approver', 'Expense approver role', true, NOW(), NOW())
        """, approver_role_id, tenant_id)
        
        submitter_role_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
            VALUES ($1, $2, 'submitter', 'Expense submitter role', true, NOW(), NOW())
        """, submitter_role_id, tenant_id)
        
        # Assign permissions to admin role
        for perm_id in permissions.values():
            await conn.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, admin_role_id, perm_id)
        
        # Assign permissions to approver role
        await conn.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES ($1, $2), ($1, $3)
            ON CONFLICT DO NOTHING
        """, approver_role_id, permissions['expense:read'], permissions['expense:approve'])
        
        # Assign permissions to submitter role
        await conn.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES ($1, $2), ($1, $3), ($1, $4), ($1, $5)
            ON CONFLICT DO NOTHING
        """, submitter_role_id, 
            permissions['expense:create'], 
            permissions['expense:read'],
            permissions['expense:update'],
            permissions['expense:delete'])
        
        # Create users
        admin_user_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
            VALUES ($1, $2, 'admin@example.com', 'Admin', 'User', $3, 'active', NOW(), NOW())
        """, admin_user_id, tenant_id, password_hash)
        
        approver_user_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
            VALUES ($1, $2, 'approver@example.com', 'Approver', 'User', $3, 'active', NOW(), NOW())
        """, approver_user_id, tenant_id, password_hash)
        
        submitter_user_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
            VALUES ($1, $2, 'user@example.com', 'Test', 'User', $3, 'active', NOW(), NOW())
        """, submitter_user_id, tenant_id, password_hash)
        
        # Assign roles
        await conn.execute("""
            INSERT INTO user_roles (user_id, role_id, assigned_at)
            VALUES ($1, $2, NOW()), ($3, $4, NOW()), ($5, $6, NOW())
            ON CONFLICT DO NOTHING
        """, admin_user_id, admin_role_id,
            approver_user_id, approver_role_id,
            submitter_user_id, submitter_role_id)
        
        print("✅ Seed data created successfully!")
        print("\nDefault users created:")
        print("  - admin@example.com / password (Admin)")
        print("  - approver@example.com / password (Approver)")
        print("  - user@example.com / password (Submitter)")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_data())

