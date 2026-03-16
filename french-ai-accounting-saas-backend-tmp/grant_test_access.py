#!/usr/bin/env python3
"""
Quick script to grant full access to admin user for testing
Run this in Docker: docker-compose exec backend-auth python grant_test_access.py
"""
import asyncio
import asyncpg
import bcrypt
import uuid
import os

async def grant_test_access():
    """Grant full access to admin user"""
    # Try Docker postgres first, then localhost
    try:
        conn = await asyncpg.connect(
            host='postgres', port=5432,
            user='dou_user', password='dou_password',
            database='dou_expense_audit'
        )
        print("✅ Connected to database (Docker)")
    except:
        try:
            conn = await asyncpg.connect(
                host='localhost', port=5432,
                user='dou_user', password='dou_password',
                database='dou_expense_audit'
            )
            print("✅ Connected to database (localhost)")
        except Exception as e:
            print(f"❌ Error connecting: {e}")
            return
    
    try:
        print("\n" + "="*70)
        print("🔐 GRANTING FULL ACCESS TO ADMIN USER FOR TESTING")
        print("="*70 + "\n")
        
        # Get or create admin user
        admin = await conn.fetchrow(
            "SELECT id, tenant_id FROM users WHERE email = $1",
            'admin@example.com'
        )
        
        if not admin:
            print("📝 Creating admin user...")
            pwd = bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode()
            tenant = await conn.fetchval("SELECT id FROM tenants LIMIT 1")
            if not tenant:
                tenant = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO tenants (id, name, slug, status, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                """, tenant, 'Default Tenant', 'default', 'active')
            uid = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """, uid, tenant, 'admin@example.com', 'Admin', 'User', pwd, 'active')
            admin = {'id': uid, 'tenant_id': tenant}
            print("✅ Admin user created")
        else:
            print("✅ Admin user found")
        
        # Get or create admin role
        role = await conn.fetchrow(
            "SELECT id FROM roles WHERE name = $1 AND tenant_id = $2",
            'admin', admin['tenant_id']
        )
        
        if not role:
            print("📝 Creating admin role...")
            rid = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            """, rid, admin['tenant_id'], 'admin', 'Admin role', True)
            role = {'id': rid}
            print("✅ Admin role created")
        else:
            print("✅ Admin role found")
        
        # Assign role to user
        await conn.execute("""
            INSERT INTO user_roles (user_id, role_id, assigned_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT DO NOTHING
        """, admin['id'], role['id'])
        print("✅ Role assigned to user")
        
        # Assign ALL permissions to admin role
        print("📝 Assigning ALL permissions to admin role...")
        await conn.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT $1, id FROM permissions
            ON CONFLICT DO NOTHING
        """, role['id'])
        
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM role_permissions WHERE role_id = $1",
            role['id']
        )
        
        print("\n" + "="*70)
        print("🎉 SUCCESS! Admin user now has FULL ACCESS")
        print("="*70)
        print("\n📧 Login Credentials:")
        print("   Email: admin@example.com")
        print("   Password: password")
        print(f"\n✅ Admin role has {count} permissions")
        print("\n💡 Please logout and login again to refresh permissions")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(grant_test_access())




