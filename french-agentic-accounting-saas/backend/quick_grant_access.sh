#!/bin/bash
# Quick script to grant full access to admin user
# Run this in Docker container

python -c "
import asyncio
import asyncpg
import bcrypt
import uuid

async def grant_access():
    conn = await asyncpg.connect(
        host='postgres', port=5432,
        user='dou_user', password='dou_password',
        database='dou_expense_audit'
    )
    try:
        print('🔐 Granting full access to admin user...')
        
        # Get admin user
        admin = await conn.fetchrow('SELECT id, tenant_id FROM users WHERE email = \$1', 'admin@example.com')
        if not admin:
            print('Creating admin user...')
            pwd = bcrypt.hashpw('password'.encode(), bcrypt.gensalt()).decode()
            tenant = await conn.fetchval('SELECT id FROM tenants LIMIT 1')
            uid = str(uuid.uuid4())
            await conn.execute('''
                INSERT INTO users (id, tenant_id, email, first_name, last_name, password_hash, status, created_at, updated_at)
                VALUES (\$1, \$2, \$3, \$4, \$5, \$6, \$7, NOW(), NOW())
            ''', uid, tenant, 'admin@example.com', 'Admin', 'User', pwd, 'active')
            admin = {'id': uid, 'tenant_id': tenant}
            print('✅ Admin user created')
        else:
            print('✅ Admin user found')
        
        # Get admin role
        role = await conn.fetchrow('SELECT id FROM roles WHERE name = \$1 AND tenant_id = \$2', 'admin', admin['tenant_id'])
        if not role:
            rid = str(uuid.uuid4())
            await conn.execute('''
                INSERT INTO roles (id, tenant_id, name, description, is_system_role, created_at, updated_at)
                VALUES (\$1, \$2, \$3, \$4, \$5, NOW(), NOW())
            ''', rid, admin['tenant_id'], 'admin', 'Admin role', True)
            role = {'id': rid}
            print('✅ Admin role created')
        else:
            print('✅ Admin role found')
        
        # Assign role to user
        await conn.execute('INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (\$1, \$2, NOW()) ON CONFLICT DO NOTHING', admin['id'], role['id'])
        print('✅ Role assigned to user')
        
        # Assign ALL permissions to admin role
        result = await conn.execute('INSERT INTO role_permissions (role_id, permission_id) SELECT \$1, id FROM permissions ON CONFLICT DO NOTHING', role['id'])
        count = await conn.fetchval('SELECT COUNT(*) FROM role_permissions WHERE role_id = \$1', role['id'])
        
        print(f'✅ SUCCESS! Admin user has {count} permissions')
        print('')
        print('📧 Login Credentials:')
        print('   Email: admin@example.com')
        print('   Password: password')
        print('')
        print('💡 Please logout and login again to refresh permissions')
    finally:
        await conn.close()

asyncio.run(grant_access())
"




