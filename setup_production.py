"""
Production Database Setup for EVisionBet
Creates all required tables with indexes for optimal performance
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    print("Please set DATABASE_URL in .env file")
    sys.exit(1)

# Fix postgres:// → postgresql:// for SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"📊 Connecting to production database...")
print(f"🔗 Host: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'localhost'}")

try:
    engine = create_engine(DATABASE_URL, echo=False)
except Exception as e:
    print(f"❌ Database connection error: {e}")
    sys.exit(1)

# Enhanced SQL with all required tables
CREATE_TABLES_SQL = """
-- ================================================================
-- RAW ODDS TABLE: Wide format storage (raw_odds_pure.csv equivalent)
-- ================================================================
DROP TABLE IF EXISTS raw_odds_pure CASCADE;
CREATE TABLE raw_odds_pure (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    away_team VARCHAR(200),
    home_team VARCHAR(200),
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    odds DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- LIVE ODDS TABLE: Current odds from all bookmakers
-- ================================================================
DROP TABLE IF EXISTS live_odds CASCADE;
CREATE TABLE live_odds (
    id SERIAL PRIMARY KEY,
    extracted_at TIMESTAMP NOT NULL,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    odds DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- EV OPPORTUNITIES TABLE: Detected value bets
-- ================================================================
DROP TABLE IF EXISTS ev_opportunities CASCADE;
CREATE TABLE ev_opportunities (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    away_team VARCHAR(100),
    home_team VARCHAR(100),
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    player VARCHAR(200),
    fair_odds DECIMAL(10,4),
    best_book VARCHAR(50) NOT NULL,
    best_odds DECIMAL(10,4) NOT NULL,
    ev_percent DECIMAL(5,2) NOT NULL,
    sharp_book_count INT,
    implied_prob DECIMAL(5,2),
    stake DECIMAL(10,2),
    kelly_fraction DECIMAL(3,2) DEFAULT 0.25,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- PRICE HISTORY TABLE: Archive of all odds snapshots
-- ================================================================
DROP TABLE IF EXISTS price_history CASCADE;
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    extracted_at TIMESTAMP NOT NULL,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    odds DECIMAL(10,4) NOT NULL,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- LINE MOVEMENTS TABLE: Track price changes
-- ================================================================
DROP TABLE IF EXISTS line_movements CASCADE;
CREATE TABLE line_movements (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    player_name VARCHAR(200),
    bookmaker VARCHAR(50) NOT NULL,
    old_odds DECIMAL(10,4),
    old_extracted_at TIMESTAMP,
    new_odds DECIMAL(10,4) NOT NULL,
    new_extracted_at TIMESTAMP NOT NULL,
    price_change DECIMAL(10,4),
    price_change_percent DECIMAL(8,4),
    movement_type VARCHAR(20),
    movement_percent DECIMAL(5,2),
    is_significant BOOLEAN DEFAULT FALSE,
    significance_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- PROP ALERTS TABLE: High-value prop opportunities
-- ================================================================
DROP TABLE IF EXISTS prop_alerts CASCADE;
CREATE TABLE prop_alerts (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    player_name VARCHAR(200) NOT NULL,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    best_book VARCHAR(50) NOT NULL,
    best_odds DECIMAL(10,4) NOT NULL,
    fair_odds DECIMAL(10,4),
    ev_percent DECIMAL(5,2),
    alert_type VARCHAR(50),
    alert_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================

-- raw_odds_pure indexes
CREATE INDEX idx_raw_odds_timestamp ON raw_odds_pure(timestamp DESC);
CREATE INDEX idx_raw_odds_event ON raw_odds_pure(event_id, market);
CREATE INDEX idx_raw_odds_bookmaker ON raw_odds_pure(bookmaker);
CREATE INDEX idx_raw_odds_sport ON raw_odds_pure(sport);

-- live_odds indexes
CREATE INDEX idx_live_odds_extracted ON live_odds(extracted_at DESC);
CREATE INDEX idx_live_odds_event ON live_odds(event_id, market);
CREATE INDEX idx_live_odds_bookmaker ON live_odds(bookmaker);

-- ev_opportunities indexes
CREATE INDEX idx_ev_detected ON ev_opportunities(detected_at DESC);
CREATE INDEX idx_ev_sport ON ev_opportunities(sport);
CREATE INDEX idx_ev_market ON ev_opportunities(market);
CREATE INDEX idx_ev_percent ON ev_opportunities(ev_percent DESC);
CREATE INDEX idx_ev_event ON ev_opportunities(event_id);

-- price_history indexes
CREATE INDEX idx_price_extracted ON price_history(extracted_at DESC);
CREATE INDEX idx_price_event ON price_history(event_id, market);
CREATE INDEX idx_price_current ON price_history(is_current);

-- line_movements indexes
CREATE INDEX idx_movements_detected ON line_movements(detected_at DESC);
CREATE INDEX idx_movements_significant ON line_movements(is_significant);
CREATE INDEX idx_movements_event ON line_movements(event_id);

-- prop_alerts indexes
CREATE INDEX idx_props_detected ON prop_alerts(detected_at DESC);
CREATE INDEX idx_props_player ON prop_alerts(player_name);
CREATE INDEX idx_props_active ON prop_alerts(is_active);
"""

print("🔧 Creating database tables...")
print("⚠️  WARNING: This will DROP existing tables and recreate them!")
print()

try:
    with engine.connect() as conn:
        # Execute the entire SQL block
        conn.execute(text(CREATE_TABLES_SQL))
        conn.commit()
        
        print("✅ Database tables created successfully!")
        print()
        
        # Verify tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
        print(f"📋 Created {len(tables)} tables:")
        for table in tables:
            # Get row count
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = count_result.fetchone()[0]
            print(f"   • {table:25s} ({count} rows)")
        
        print()
        print("✅ Production database setup complete!")
        print()
        print("Next steps:")
        print("  1. Run pipeline: python src/pipeline_v2/extract_odds.py")
        print("  2. Calculate EV: python src/pipeline_v2/calculate_opportunities.py")
        print("  3. Start API: uvicorn backend_api:app --reload")
        
except Exception as e:
    print(f"❌ Error setting up database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
