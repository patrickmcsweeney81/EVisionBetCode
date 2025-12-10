-- ================================================================
-- LIVE ODDS TABLE: Current odds from all bookmakers
-- ================================================================
CREATE TABLE IF NOT EXISTS live_odds (
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
CREATE TABLE IF NOT EXISTS ev_opportunities (
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
    kelly_fraction DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- PRICE HISTORY TABLE: Archive of all odds snapshots
-- Automatically grows on each extraction - enables line tracking
-- ================================================================
CREATE TABLE IF NOT EXISTS price_history (
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
    
    -- Metadata
    is_current BOOLEAN DEFAULT TRUE,  -- Current extraction mark current=TRUE, previous=FALSE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(event_id, market, point, selection, bookmaker, extracted_at)
);

-- ================================================================
-- LINE MOVEMENTS TABLE: Track price changes between extractions
-- GREEN = Price Down (better odds for bettor)
-- RED = Price Up (worse odds for bettor)
-- ================================================================
CREATE TABLE IF NOT EXISTS line_movements (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    market VARCHAR(50) NOT NULL,
    point DECIMAL(6,1),
    selection VARCHAR(200) NOT NULL,
    player_name VARCHAR(200),  -- For prop tracking
    bookmaker VARCHAR(50) NOT NULL,
    
    -- Previous extraction
    old_odds DECIMAL(10,4),
    old_extracted_at TIMESTAMP,
    
    -- Current extraction
    new_odds DECIMAL(10,4) NOT NULL,
    new_extracted_at TIMESTAMP NOT NULL,
    
    -- Calculated deltas
    price_change DECIMAL(10,4),  -- new_odds - old_odds
    price_change_percent DECIMAL(8,4),  -- (new - old) / old * 100
    
    -- Movement classification (for UI colors)
    movement_type VARCHAR(20),  -- 'DOWN' (Green - better odds), 'UP' (Red - worse odds), 'SAME'
    movement_percent DECIMAL(5,2),  -- absolute percent change
    
    -- Significance flag
    is_significant BOOLEAN DEFAULT FALSE,  -- TRUE if movement > threshold
    significance_level VARCHAR(20),  -- 'MINOR', 'MODERATE', 'MAJOR'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- PROP ALERTS TABLE: Detected high-value player prop opportunities
-- Triggers on new props, line moves, or EV thresholds
-- ================================================================
CREATE TABLE IF NOT EXISTS prop_alerts (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sport VARCHAR(50) NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP,
    
    -- Player info
    player_name VARCHAR(200) NOT NULL,
    player_id VARCHAR(100),
    
    -- Prop details
    prop_market VARCHAR(100) NOT NULL,  -- e.g., 'player_points', 'player_assists'
    prop_line DECIMAL(6,1),  -- e.g., 23.5 points
    
    -- Odds and value
    over_odds DECIMAL(10,4),
    under_odds DECIMAL(10,4),
    best_side VARCHAR(10),  -- 'OVER' or 'UNDER'
    best_book VARCHAR(50),
    
    -- EV calculation
    ev_percent DECIMAL(5,2),
    implied_prob DECIMAL(5,2),
    
    -- Alert metadata
    alert_type VARCHAR(30),  -- 'HIGH_EV', 'LINE_MOVE', 'SHARP_SIGNAL', 'NEW_PROP'
    severity VARCHAR(10),  -- 'LOW', 'MEDIUM', 'HIGH'
    
    -- Status tracking
    is_active BOOLEAN DEFAULT TRUE,
    closed_at TIMESTAMP,  -- When prop resolved or event started
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================

-- Live Odds Indexes
CREATE INDEX IF NOT EXISTS idx_live_odds_event ON live_odds(event_id, market);
CREATE INDEX IF NOT EXISTS idx_live_odds_bookmaker ON live_odds(bookmaker);
CREATE INDEX IF NOT EXISTS idx_live_odds_extracted ON live_odds(extracted_at);
CREATE INDEX IF NOT EXISTS idx_live_odds_sport ON live_odds(sport);

-- EV Opportunities Indexes
CREATE INDEX IF NOT EXISTS idx_ev_detected ON ev_opportunities(detected_at);
CREATE INDEX IF NOT EXISTS idx_ev_sport ON ev_opportunities(sport);
CREATE INDEX IF NOT EXISTS idx_ev_percent ON ev_opportunities(ev_percent);
CREATE INDEX IF NOT EXISTS idx_ev_event ON ev_opportunities(event_id, market);

-- Price History Indexes
CREATE INDEX IF NOT EXISTS idx_price_history_extracted ON price_history(extracted_at);
CREATE INDEX IF NOT EXISTS idx_price_history_event ON price_history(event_id, market, selection);
CREATE INDEX IF NOT EXISTS idx_price_history_current ON price_history(is_current);
CREATE INDEX IF NOT EXISTS idx_price_history_bookmaker ON price_history(bookmaker);

-- Line Movements Indexes (most frequently queried)
CREATE INDEX IF NOT EXISTS idx_line_movements_detected ON line_movements(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_line_movements_event ON line_movements(event_id, market);
CREATE INDEX IF NOT EXISTS idx_line_movements_type ON line_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_line_movements_bookmaker ON line_movements(bookmaker);
CREATE INDEX IF NOT EXISTS idx_line_movements_significant ON line_movements(is_significant);
CREATE INDEX IF NOT EXISTS idx_line_movements_player ON line_movements(player_name);

-- Prop Alerts Indexes
CREATE INDEX IF NOT EXISTS idx_prop_alerts_detected ON prop_alerts(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_prop_alerts_player ON prop_alerts(player_name);
CREATE INDEX IF NOT EXISTS idx_prop_alerts_sport ON prop_alerts(sport);
CREATE INDEX IF NOT EXISTS idx_prop_alerts_severity ON prop_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_prop_alerts_active ON prop_alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_prop_alerts_type ON prop_alerts(alert_type);
