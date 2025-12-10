"""
Verify that data is flowing into the Render PostgreSQL database
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

print("📊 Connecting to Render PostgreSQL...\n")

try:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name IN ('live_odds', 'ev_opportunities')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"✅ Tables Found: {', '.join(tables) if tables else 'None yet'}")
    
    if 'live_odds' in tables:
        # Check live_odds data
        cursor.execute("SELECT COUNT(*) FROM live_odds")
        count = cursor.fetchone()[0]
        print(f"\n📈 live_odds table:")
        print(f"   Total rows: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT extracted_at, sport, COUNT(*) as cnt 
                FROM live_odds 
                GROUP BY extracted_at, sport 
                ORDER BY extracted_at DESC 
                LIMIT 5
            """)
            print(f"   Latest extractions:")
            for row in cursor.fetchall():
                print(f"     - {row[0]} ({row[1]}): {row[2]} rows")
    
    if 'ev_opportunities' in tables:
        # Check ev_opportunities data
        cursor.execute("SELECT COUNT(*) FROM ev_opportunities")
        count = cursor.fetchone()[0]
        print(f"\n💡 ev_opportunities table:")
        print(f"   Total opportunities: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT sport, COUNT(*) as cnt, AVG(ev_percent) as avg_ev
                FROM ev_opportunities 
                GROUP BY sport 
                ORDER BY cnt DESC
            """)
            print(f"   Opportunities by sport:")
            for sport, cnt, avg_ev in cursor.fetchall():
                print(f"     - {sport}: {cnt} opps (avg EV: {avg_ev:.2f}%)")
            
            cursor.execute("""
                SELECT selection, best_book, ev_percent 
                FROM ev_opportunities 
                ORDER BY ev_percent DESC 
                LIMIT 3
            """)
            print(f"\n   🏆 Top 3 EV opportunities:")
            for sel, book, ev in cursor.fetchall():
                print(f"     {ev:.2f}% @ {book}: {sel}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Database verification complete!")
    
except ImportError:
    print("❌ psycopg2 not installed. Installing...")
    os.system("pip install psycopg2-binary -q")
    print("Please run this script again!")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n⚠️  This is expected if:")
    print("   - Cron jobs haven't run yet (wait a few minutes)")
    print("   - Database connection is blocked")
    print("   - Tables haven't been created yet")
