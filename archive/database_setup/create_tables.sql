
-- ================================================================
-- LIVE ODDS TABLE: Current odds from all bookmakers
-- ================================================================
IF OBJECT_ID('live_odds', 'U') IS NULL
BEGIN
	CREATE TABLE live_odds (
		id INT IDENTITY(1,1) PRIMARY KEY,
		extracted_at DATETIME NOT NULL,
		sport VARCHAR(50) NOT NULL,
		event_id VARCHAR(100) NOT NULL,
		commence_time DATETIME,
		market VARCHAR(50) NOT NULL,
		point DECIMAL(6,1),
		selection VARCHAR(200) NOT NULL,
		bookmaker VARCHAR(50) NOT NULL,
		odds DECIMAL(10,4) NOT NULL,
		created_at DATETIME DEFAULT GETDATE()
	)
END
GO

-- ================================================================
-- EV OPPORTUNITIES TABLE: Detected value bets
-- ================================================================
IF OBJECT_ID('ev_opportunities', 'U') IS NULL
BEGIN
	CREATE TABLE ev_opportunities (
		id INT IDENTITY(1,1) PRIMARY KEY,
		detected_at DATETIME NOT NULL,
		sport VARCHAR(50) NOT NULL,
		event_id VARCHAR(100) NOT NULL,
		away_team VARCHAR(100),
		home_team VARCHAR(100),
		commence_time DATETIME,
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
		created_at DATETIME DEFAULT GETDATE()
	)
END
GO

-- ================================================================
-- PRICE HISTORY TABLE: Archive of all odds snapshots
-- Automatically grows on each extraction - enables line tracking
-- ================================================================
IF OBJECT_ID('price_history', 'U') IS NULL
BEGIN
	CREATE TABLE price_history (
		id INT IDENTITY(1,1) PRIMARY KEY,
		extracted_at DATETIME NOT NULL,
		sport VARCHAR(50) NOT NULL,
		event_id VARCHAR(100) NOT NULL,
		commence_time DATETIME,
		market VARCHAR(50) NOT NULL,
		point DECIMAL(6,1),
		selection VARCHAR(200) NOT NULL,
		bookmaker VARCHAR(50) NOT NULL,
		odds DECIMAL(10,4) NOT NULL,
		is_current BIT DEFAULT 1,  -- Current extraction mark current=1, previous=0
		created_at DATETIME DEFAULT GETDATE(),
		CONSTRAINT uq_price_history UNIQUE(event_id, market, point, selection, bookmaker, extracted_at)
	)
END
GO

-- ================================================================
-- LINE MOVEMENTS TABLE: Track price changes between extractions
-- GREEN = Price Down (better odds for bettor)
-- RED = Price Up (worse odds for bettor)
-- ================================================================
IF OBJECT_ID('line_movements', 'U') IS NULL
BEGIN
	CREATE TABLE line_movements (
		id INT IDENTITY(1,1) PRIMARY KEY,
		detected_at DATETIME NOT NULL DEFAULT GETDATE(),
		sport VARCHAR(50) NOT NULL,
		event_id VARCHAR(100) NOT NULL,
		commence_time DATETIME,
		market VARCHAR(50) NOT NULL,
		point DECIMAL(6,1),
		selection VARCHAR(200) NOT NULL,
		player_name VARCHAR(200),  -- For prop tracking
		bookmaker VARCHAR(50) NOT NULL,
		old_odds DECIMAL(10,4),
		old_extracted_at DATETIME,
		new_odds DECIMAL(10,4) NOT NULL,
		new_extracted_at DATETIME NOT NULL,
		price_change DECIMAL(10,4),  -- new_odds - old_odds
		price_change_percent DECIMAL(8,4),  -- (new - old) / old * 100
		movement_type VARCHAR(20),  -- 'DOWN', 'UP', 'SAME'
		movement_percent DECIMAL(5,2),
		is_significant BIT DEFAULT 0,  -- 1 if movement > threshold
		significance_level VARCHAR(20),
		created_at DATETIME DEFAULT GETDATE()
	)
END
GO

-- ================================================================
-- PROP ALERTS TABLE: Detected high-value player prop opportunities
-- Triggers on new props, line moves, or EV thresholds
-- ================================================================
IF OBJECT_ID('prop_alerts', 'U') IS NULL
BEGIN
	CREATE TABLE prop_alerts (
		id INT IDENTITY(1,1) PRIMARY KEY,
		detected_at DATETIME NOT NULL DEFAULT GETDATE(),
		sport VARCHAR(50) NOT NULL,
		event_id VARCHAR(100) NOT NULL,
		commence_time DATETIME,
		player_name VARCHAR(200) NOT NULL,
		player_id VARCHAR(100),
		prop_market VARCHAR(100) NOT NULL,
		prop_line DECIMAL(6,1),
		over_odds DECIMAL(10,4),
		under_odds DECIMAL(10,4),
		best_side VARCHAR(10),
		best_book VARCHAR(50),
		ev_percent DECIMAL(5,2),
		implied_prob DECIMAL(5,2),
		alert_type VARCHAR(30),
		severity VARCHAR(10),
		is_active BIT DEFAULT 1,
		closed_at DATETIME,
		created_at DATETIME DEFAULT GETDATE()
	)
END
GO

-- ================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================


IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_live_odds_event')
	CREATE INDEX idx_live_odds_event ON live_odds(event_id, market);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_live_odds_bookmaker')
	CREATE INDEX idx_live_odds_bookmaker ON live_odds(bookmaker);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_live_odds_extracted')
	CREATE INDEX idx_live_odds_extracted ON live_odds(extracted_at);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_live_odds_sport')
	CREATE INDEX idx_live_odds_sport ON live_odds(sport);
GO


IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_ev_detected')
	CREATE INDEX idx_ev_detected ON ev_opportunities(detected_at);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_ev_sport')
	CREATE INDEX idx_ev_sport ON ev_opportunities(sport);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_ev_percent')
	CREATE INDEX idx_ev_percent ON ev_opportunities(ev_percent);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_ev_event')
	CREATE INDEX idx_ev_event ON ev_opportunities(event_id, market);
GO


IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_price_history_extracted')
	CREATE INDEX idx_price_history_extracted ON price_history(extracted_at);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_price_history_event')
	CREATE INDEX idx_price_history_event ON price_history(event_id, market, selection);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_price_history_current')
	CREATE INDEX idx_price_history_current ON price_history(is_current);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_price_history_bookmaker')
	CREATE INDEX idx_price_history_bookmaker ON price_history(bookmaker);
GO


IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_line_movements_detected')
	CREATE INDEX idx_line_movements_detected ON line_movements(detected_at DESC);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_line_movements_event')
	CREATE INDEX idx_line_movements_event ON line_movements(event_id, market);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_line_movements_type')
	CREATE INDEX idx_line_movements_type ON line_movements(movement_type);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_line_movements_bookmaker')
	CREATE INDEX idx_line_movements_bookmaker ON line_movements(bookmaker);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_line_movements_significant')
	CREATE INDEX idx_line_movements_significant ON line_movements(is_significant);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_line_movements_player')
	CREATE INDEX idx_line_movements_player ON line_movements(player_name);
GO


IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_prop_alerts_detected')
	CREATE INDEX idx_prop_alerts_detected ON prop_alerts(detected_at DESC);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_prop_alerts_player')
	CREATE INDEX idx_prop_alerts_player ON prop_alerts(player_name);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_prop_alerts_sport')
	CREATE INDEX idx_prop_alerts_sport ON prop_alerts(sport);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_prop_alerts_severity')
	CREATE INDEX idx_prop_alerts_severity ON prop_alerts(severity);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_prop_alerts_active')
	CREATE INDEX idx_prop_alerts_active ON prop_alerts(is_active);
GO
IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name = 'idx_prop_alerts_type')
	CREATE INDEX idx_prop_alerts_type ON prop_alerts(alert_type);
GO

-- End of schema definition

