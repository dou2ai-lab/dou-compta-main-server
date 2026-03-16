# -----------------------------------------------------------------------------
# File: grant_full_access.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Grant full access to admin user for testing all components
# -----------------------------------------------------------------------------

"""
Script to grant FULL ACCESS to admin user for testing
This ensures admin@example.com has ALL permissions for ALL services
"""
import asyncio
import asyncpg
import sys
import os

# Database connection settings
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_USER = os.getenv('DB_USER', 'dou_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'dou_password')
DB_NAME = os.getenv('DB_NAME', 'dou_expense_audit')

async def grant_full_access():
    """Grant full access to admin user"""
    # Try connecting to postgres (Docker) first, fallback to localhost
    conn = None
    try:
        conn = await asyncpg.connect(
            host='postgres',
            port=5432,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("✅ Connected to database (Docker)")
    except Exception as e:
        print(f"⚠️  Could not connect to Docker postgres: {e}")
        print("🔄 Trying localhost...")
        try:
            conn = await asyncpg.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            print("✅ Connected to database (localhost)")
        except Exception as e2:
            print(f"❌ Error connecting to database: {e2}")
            print("\n💡 Make sure PostgreSQL is running and accessible")
            print("   Docker: docker-compose -f infrastructure/docker-compose.yml up -d postgres")
            sys.exit(1)
    
    try:
        print("\n" + "="*70)
        print("🔐 GRANTING FULL ACCESS TO ADMIN USER FOR TESTING")
        print("="*70 + "\n")
        
        # Get or create admin user
        admin_user = await conn.fetchrow(
            "SELECT id, email, tenant_id FROM users WHERE email = $1 AND (deleted_at IS NULL OR deleted_at > NOW())",
            'admin@example.com'
        )
        
        if not admin_user:
            print("📝 Admin user not found. Creating admin user...")
            import bcrypt
            import uuid
            password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()
            
            # Get or create tenant
            tenant = await conn.fetchrow("SELECT id FROM tenants WHERE deleted_at IS NULL LIMIT 1")
            if not tenant:
                tenant_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO tenants (id, name, slug, status, created_at, updated_at)
                    VALUES ($1, 'Default Tenant', 'default', 'active', NOW(), NOW())
                """, tenant_id)
                print(f"✅ Created default tenant: {tenant_id}")
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
            print(f"✅ Found admin user: {admin_user['email']} (ID: {admin_user['id']})")
        
        # Get or create admin role
        admin_role = await conn.fetchrow(
            "SELECT id FROM roles WHERE name = 'admin' AND tenant_id = $1 AND (deleted_at IS NULL OR deleted_at > NOW())",
            admin_user['tenant_id']
        )
        
        if not admin_role:
            print("📝 Admin role not found. Creating admin role...")
            import uuid
            admin_role_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
                VALUES ($1, $2, 'admin', 'Administrator role with full access', true, NOW(), NOW())
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
        
        # Define ALL permissions needed for testing
        all_permissions = [
            # Expense permissions
            ('expense:create', 'Create expenses', 'expense', 'create'),
            ('expense:read', 'Read expenses', 'expense', 'read'),
            ('expense:update', 'Update expenses', 'expense', 'update'),
            ('expense:delete', 'Delete expenses', 'expense', 'delete'),
            ('expense:approve', 'Approve expenses', 'expense', 'approve'),
            ('expense:submit', 'Submit expenses', 'expense', 'submit'),
            
            # Admin permissions
            ('admin:read', 'Read admin settings', 'admin', 'read'),
            ('admin:write', 'Write admin settings', 'admin', 'write'),
            
            # User permissions
            ('user:read', 'Read users', 'user', 'read'),
            ('user:write', 'Write users', 'user', 'write'),
            ('user:create', 'Create users', 'user', 'create'),
            ('user:delete', 'Delete users', 'user', 'delete'),
            
            # Audit permissions
            ('audit:read', 'Read audit logs', 'audit', 'read'),
            ('audit:write', 'Write audit logs', 'audit', 'write'),
            ('audit:create', 'Create audit reports', 'audit', 'create'),
            ('audit:generate', 'Generate audit reports', 'audit', 'generate'),
            
            # Report permissions
            ('report:read', 'Read reports', 'report', 'read'),
            ('report:write', 'Write reports', 'report', 'write'),
            ('report:create', 'Create reports', 'report', 'create'),
            ('report:approve', 'Approve reports', 'report', 'approve'),
            
            # Policy permissions
            ('policy:read', 'Read policies', 'policy', 'read'),
            ('policy:write', 'Write policies', 'policy', 'write'),
            ('policy:create', 'Create policies', 'policy', 'create'),
            ('policy:delete', 'Delete policies', 'policy', 'delete'),
            
            # File/Receipt permissions
            ('file:read', 'Read files', 'file', 'read'),
            ('file:write', 'Write files', 'file', 'write'),
            ('file:upload', 'Upload files', 'file', 'upload'),
            ('file:delete', 'Delete files', 'file', 'delete'),
            
            # OCR permissions
            ('ocr:read', 'Read OCR results', 'ocr', 'read'),
            ('ocr:process', 'Process OCR', 'ocr', 'process'),
            
            # LLM permissions
            ('llm:read', 'Read LLM results', 'llm', 'read'),
            ('llm:extract', 'Extract with LLM', 'llm', 'extract'),
            
            # Anomaly detection permissions
            ('anomaly:read', 'Read anomaly results', 'anomaly', 'read'),
            ('anomaly:analyze', 'Analyze anomalies', 'anomaly', 'analyze'),
            ('anomaly:train', 'Train anomaly models', 'anomaly', 'train'),
            
            # RAG permissions
            ('rag:read', 'Read RAG results', 'rag', 'read'),
            ('rag:query', 'Query RAG', 'rag', 'query'),
            ('rag:embed', 'Embed documents', 'rag', 'embed'),
            
            # ERP permissions
            ('erp:read', 'Read ERP data', 'erp', 'read'),
            ('erp:write', 'Write ERP data', 'erp', 'write'),
            ('erp:connect', 'Connect to ERP', 'erp', 'connect'),
            ('erp:post', 'Post to ERP', 'erp', 'post'),
            
            # GDPR permissions
            ('gdpr:read', 'Read GDPR data', 'gdpr', 'read'),
            ('gdpr:write', 'Write GDPR data', 'gdpr', 'write'),
            ('gdpr:request', 'Handle GDPR requests', 'gdpr', 'request'),
            
            # Monitoring permissions
            ('monitoring:read', 'Read monitoring data', 'monitoring', 'read'),
            ('monitoring:write', 'Write monitoring data', 'monitoring', 'write'),
            ('monitoring:manage', 'Manage monitoring', 'monitoring', 'manage'),
            
            # Security permissions
            ('security:read', 'Read security logs', 'security', 'read'),
            ('security:write', 'Write security logs', 'security', 'write'),
            
            # Performance permissions
            ('performance:read', 'Read performance data', 'performance', 'read'),
            ('performance:manage', 'Manage performance', 'performance', 'manage'),
        ]
        
        # Create all permissions if they don't exist
        print("\n📝 Ensuring all permissions exist...")
        created_count = 0
        for name, desc, resource, action in all_permissions:
            existing = await conn.fetchrow(
                "SELECT id FROM permissions WHERE name = $1",
                name
            )
            if not existing:
                import uuid
                perm_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO permissions (id, name, description, resource, action, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (name) DO NOTHING
                """, perm_id, name, desc, resource, action)
                created_count += 1
        
        if created_count > 0:
            print(f"✅ Created {created_count} new permissions")
        else:
            print("✅ All permissions already exist")
        
        # Get all permissions (including newly created ones)
        all_perms = await conn.fetch("SELECT id, name FROM permissions")
        print(f"📊 Total permissions in system: {len(all_perms)}")
        
        # Assign ALL permissions to admin role
        print("\n📝 Assigning ALL permissions to admin role...")
        assigned_count = 0
        for perm in all_perms:
            result = await conn.execute("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, admin_role['id'], perm['id'])
            if '1' in str(result) or 'INSERT' in str(result):
                assigned_count += 1
        
        print(f"✅ Assigned {assigned_count} permissions to admin role")
        print(f"   Total permissions available: {len(all_perms)}")
        
        # Verify permissions
        print("\n🔍 Verifying permissions...")
        user_perms = await conn.fetch("""
            SELECT DISTINCT p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = $1
            ORDER BY p.name
        """, admin_user['id'])
        
        print(f"✅ Admin user has {len(user_perms)} permissions:")
        for perm in user_perms[:10]:  # Show first 10
            print(f"   - {perm['name']}")
        if len(user_perms) > 10:
            print(f"   ... and {len(user_perms) - 10} more")
        
        print("\n" + "="*70)
        print("🎉 SUCCESS! Admin user now has FULL ACCESS")
        print("="*70)
        print("\n📧 Login Credentials:")
        print("   Email: admin@example.com")
        print("   Password: password")
        print("\n✅ This user now has access to:")
        print("   - All expenses (create, read, update, delete, approve)")
        print("   - Admin panel (read, write)")
        print("   - Audit logs and reports (read, write, create, generate)")
        print("   - User management (read, write, create, delete)")
        print("   - Reports (read, write, create, approve)")
        print("   - Policies (read, write, create, delete)")
        print("   - File uploads and receipts")
        print("   - OCR and LLM services")
        print("   - Anomaly detection")
        print("   - RAG and Q&A")
        print("   - ERP integration")
        print("   - GDPR compliance")
        print("   - Monitoring dashboard")
        print("   - Security logs")
        print("   - Performance management")
        print("\n💡 Please log out and log in again to refresh permissions.")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(grant_full_access())




