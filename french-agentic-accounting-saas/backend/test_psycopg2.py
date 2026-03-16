"""Test connection with psycopg2 (synchronous)"""
import psycopg2
import sys

try:
    print("Testing connection with psycopg2...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='dou_user',
        password='dou_password123',
        database='dou_expense_audit'
    )
    print("✅ Connected successfully!")
    
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE email = %s", ('admin@example.com',))
    user = cur.fetchone()
    
    if user:
        print(f"✅ User found: {user[0]}")
    else:
        print("❌ User not found")
    
    cur.close()
    conn.close()
    print("✅ Connection closed")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
