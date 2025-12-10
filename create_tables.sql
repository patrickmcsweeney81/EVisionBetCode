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
    odds DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX IF NOT EXISTS idx_live_odds_event ON live_odds(event_id, market);
CREATE INDEX IF NOT EXISTS idx_live_odds_bookmaker ON live_odds(bookmaker);
CREATE INDEX IF NOT EXISTS idx_live_odds_extracted ON live_odds(extracted_at);
CREATE INDEX IF NOT EXISTS idx_ev_detected ON ev_opportunities(detected_at);
CREATE INDEX IF NOT EXISTS idx_ev_sport ON ev_opportunities(sport);
CREATE INDEX IF NOT EXISTS idx_ev_percent ON ev_opportunities(ev_percent);
