"""
Execute create_tables.sql against Render PostgreSQL database
"""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

# Read SQL file
with open("create_tables.sql", "r") as f:
    sql_content = f.read()

# Connect and execute
try:
    import psycopg2
    
    # Parse connection string
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("📊 Executing SQL...")
    cursor.execute(sql_content)
    conn.commit()
    
    print("✅ Tables created successfully!")
    
    # Verify
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    print(f"📋 Tables: {[t[0] for t in tables]}")
    
    cursor.close()
    conn.close()
    
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    os.system("pip install psycopg2-binary")
    print("Please run this script again!")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
