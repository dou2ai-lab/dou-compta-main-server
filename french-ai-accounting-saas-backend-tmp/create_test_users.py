"""
Quick script to create test users
"""
import asyncio
import asyncpg
import bcrypt
import uuid

async def create_test_users():
    """Create test users in the database"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='dou_user',
            password='dou_password123',
            database='dou_expense_audit'
        )
        print("Connected to database")
        
        # Get or create tenant
        tenant = await conn.fetchrow("SELECT id FROM tenants LIMIT 1")
        if not tenant:
            tenant_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO tenants (id, name, slug, status, created_at, updated_at)
                VALUES ($1, 'Default Tenant', 'default', 'active', NOW(), NOW())
            """, tenant_id)
            print(f"Created tenant: {tenant_id}")
        else:
            tenant_id = tenant['id']
            print(f"Using existing tenant: {tenant_id}")
        
        # Hash password
        password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()
        
        # Create admin user
        admin_exists = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", 'admin@example.com'
        )
        if not admin_exists:
            admin_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
                VALUES ($1, $2, 'admin@example.com', 'Admin', 'User', $3, 'active', NOW(), NOW())
            """, admin_id, tenant_id, password_hash)
            print("Created admin user: admin@example.com / password")
        else:
            print("Admin user already exists")
        
        # Create submitter user
        user_exists = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", 'user@example.com'
        )
        if not user_exists:
            user_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
                VALUES ($1, $2, 'user@example.com', 'Test', 'User', $3, 'active', NOW(), NOW())
            """, user_id, tenant_id, password_hash)
            print("Created submitter user: user@example.com / password")
        else:
            print("Submitter user already exists")
        
        print("\nTest users created successfully!")
        print("Credentials:")
        print("  - admin@example.com / password (Admin)")
        print("  - user@example.com / password (Submitter)")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_users())
