"""
FastAPI backend service for EV_ARB Bot
Exposes PostgreSQL data to frontend via REST API
Runs on Render as a Web Service (not cron job)
"""

import os
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Replace postgres:// with postgresql:// for SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class LiveOdds(Base):
    """Raw odds from all bookmakers"""
    __tablename__ = "live_odds"

    id = Column(Integer, primary_key=True)
    extracted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    commence_time = Column(DateTime)
    market = Column(String, nullable=False)
    point = Column(Float)
    selection = Column(String, nullable=False)
    bookmaker = Column(String, nullable=False)
    odds = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "commence_time": self.commence_time.isoformat() if self.commence_time else None,
            "market": self.market,
            "point": self.point,
            "selection": self.selection,
            "bookmaker": self.bookmaker,
            "odds": self.odds,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EVOpportunity(Base):
    """EV opportunities above threshold"""
    __tablename__ = "ev_opportunities"

    id = Column(Integer, primary_key=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    away_team = Column(String)
    home_team = Column(String)
    commence_time = Column(DateTime)
    market = Column(String, nullable=False)
    point = Column(Float)
    selection = Column(String, nullable=False)
    player = Column(String)
    fair_odds = Column(Float)
    best_book = Column(String, nullable=False)
    best_odds = Column(Float, nullable=False)
    ev_percent = Column(Float, nullable=False)  # stored as percent (e.g., 5.0 for 5%)
    sharp_book_count = Column(Integer, default=0)
    implied_prob = Column(Float)
    stake = Column(Float)
    kelly_fraction = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "away_team": self.away_team,
            "home_team": self.home_team,
            "commence_time": self.commence_time.isoformat() if self.commence_time else None,
            "market": self.market,
            "point": self.point,
            "selection": self.selection,
            "player": self.player,
            "fair_odds": round(self.fair_odds, 2) if self.fair_odds else None,
            "best_odds": round(self.best_odds, 2) if self.best_odds else None,
            "best_book": self.best_book,
            "ev_percent": round(self.ev_percent, 2),
            "sharp_book_count": self.sharp_book_count,
            "implied_prob": round(self.implied_prob, 2) if self.implied_prob else None,
            "stake": round(self.stake, 2) if self.stake else None,
            "kelly_fraction": self.kelly_fraction,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PriceHistory(Base):
    """Historical odds archive - enables line movement tracking"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    extracted_at = Column(DateTime, nullable=False)
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    commence_time = Column(DateTime)
    market = Column(String, nullable=False)
    point = Column(Float)
    selection = Column(String, nullable=False)
    bookmaker = Column(String, nullable=False)
    odds = Column(Float, nullable=False)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "market": self.market,
            "point": self.point,
            "selection": self.selection,
            "bookmaker": self.bookmaker,
            "odds": round(self.odds, 4) if self.odds else None,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "is_current": self.is_current,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LineMovement(Base):
    """Line movements - price changes between extractions (GREEN/RED alerts)"""
    __tablename__ = "line_movements"

    id = Column(Integer, primary_key=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    commence_time = Column(DateTime)
    market = Column(String, nullable=False)
    point = Column(Float)
    selection = Column(String, nullable=False)
    player_name = Column(String)
    bookmaker = Column(String, nullable=False)
    
    # Price data
    old_odds = Column(Float)
    old_extracted_at = Column(DateTime)
    new_odds = Column(Float, nullable=False)
    new_extracted_at = Column(DateTime, nullable=False)
    
    # Deltas
    price_change = Column(Float)
    price_change_percent = Column(Float)
    
    # Classification
    movement_type = Column(String)  # 'DOWN' (Green), 'UP' (Red), 'SAME'
    movement_percent = Column(Float)
    is_significant = Column(Boolean, default=False)
    significance_level = Column(String)  # 'MINOR', 'MODERATE', 'MAJOR'
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "market": self.market,
            "point": self.point,
            "selection": self.selection,
            "bookmaker": self.bookmaker,
            "player_name": self.player_name,
            "old_odds": round(self.old_odds, 4) if self.old_odds else None,
            "new_odds": round(self.new_odds, 4) if self.new_odds else None,
            "price_change": round(self.price_change, 4) if self.price_change else None,
            "price_change_percent": round(self.price_change_percent, 2) if self.price_change_percent else None,
            "movement_type": self.movement_type,  # 'DOWN' (Green), 'UP' (Red)
            "is_significant": self.is_significant,
            "significance_level": self.significance_level,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class PropAlert(Base):
    """Player prop alerts - high-value prop opportunities"""
    __tablename__ = "prop_alerts"

    id = Column(Integer, primary_key=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    commence_time = Column(DateTime)
    
    # Player
    player_name = Column(String, nullable=False)
    player_id = Column(String)
    
    # Prop details
    prop_market = Column(String, nullable=False)  # 'player_points', 'player_assists', etc.
    prop_line = Column(Float)
    
    # Odds
    over_odds = Column(Float)
    under_odds = Column(Float)
    best_side = Column(String)  # 'OVER' or 'UNDER'
    best_book = Column(String)
    
    # EV
    ev_percent = Column(Float)
    implied_prob = Column(Float)
    
    # Alert type
    alert_type = Column(String)  # 'HIGH_EV', 'LINE_MOVE', 'SHARP_SIGNAL', 'NEW_PROP'
    severity = Column(String)  # 'LOW', 'MEDIUM', 'HIGH'
    
    # Status
    is_active = Column(Boolean, default=True)
    closed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "player_name": self.player_name,
            "prop_market": self.prop_market,
            "prop_line": self.prop_line,
            "over_odds": round(self.over_odds, 4) if self.over_odds else None,
            "under_odds": round(self.under_odds, 4) if self.under_odds else None,
            "best_side": self.best_side,
            "best_book": self.best_book,
            "ev_percent": round(self.ev_percent, 2) if self.ev_percent else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "is_active": self.is_active,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="EV_ARB Bot API",
    description="Sports betting expected value finder backend",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    session = SessionLocal()
    try:
        # Simple DB connectivity probe
        session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }
    finally:
        session.close()

# ============================================================================
# EV HITS ENDPOINTS
# ============================================================================

@app.get("/api/ev/hits")
async def get_ev_hits(
    limit: int = Query(50, ge=1, le=1000),
    min_ev: float = Query(0.01, ge=0),
    sport: Optional[str] = Query(None),
):
    """
    Get EV opportunities filtered by criteria
    
    Args:
        limit: Max results (default 50)
        min_ev: Minimum EV as decimal (default 0.01 = 1%)
        sport: Filter by sport (basketball_nba, americanfootball_nfl, etc.)
    """
    try:
        session = SessionLocal()
        
        # Build query
        query = session.query(EVOpportunity).filter(
            EVOpportunity.ev_percent >= min_ev
        )
        
        # Apply sport filter if provided
        if sport:
            query = query.filter(EVOpportunity.sport == sport)
        
        # Order by EV descending, limit results
        hits = query.order_by(EVOpportunity.ev_percent.desc()).limit(limit).all()
        
        # Get summary stats
        all_hits = session.query(EVOpportunity).all()
        sports_dict = {}
        for hit in all_hits:
            if hit.sport not in sports_dict:
                sports_dict[hit.sport] = 0
            sports_dict[hit.sport] += 1
        
        last_updated = None
        if hits:
            last_updated = max((h.detected_at or h.created_at) for h in hits).isoformat()
        
        session.close()
        
        return {
            "hits": [h.to_dict() for h in hits],
            "count": len(hits),
            "last_updated": last_updated or datetime.utcnow().isoformat(),
            "filters": {
                "limit": limit,
                "min_ev": min_ev,
                "sport": sport
            }
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "hits": [],
            "count": 0,
            "last_updated": datetime.utcnow().isoformat()
        }


@app.get("/api/ev/summary")
async def get_ev_summary():
    """Get summary stats about EV opportunities"""
    try:
        session = SessionLocal()
        
        # Query all EV opportunities
        all_hits = session.query(EVOpportunity).all()
        
        if not all_hits:
            return {
                "available": False,
                "total_hits": 0,
                "top_ev": 0,
                "sports": {},
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Calculate summary stats
        sports_dict = {}
        top_ev = 0
        
        for hit in all_hits:
            # Count by sport
            if hit.sport not in sports_dict:
                sports_dict[hit.sport] = 0
            sports_dict[hit.sport] += 1
            
            # Track highest EV
            if hit.ev_percent > top_ev:
                top_ev = hit.ev_percent

        last_updated = max((h.detected_at or h.created_at) for h in all_hits).isoformat()
        
        session.close()
        
        return {
            "available": True,
            "total_hits": len(all_hits),
            "top_ev": round(top_ev, 2),
            "sports": sports_dict,
            "last_updated": last_updated
        }
    
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "total_hits": 0,
            "top_ev": 0,
            "sports": {},
            "last_updated": datetime.utcnow().isoformat()
        }


# ============================================================================
# ODDS ENDPOINTS
# ============================================================================

@app.get("/api/odds/latest")
async def get_latest_odds(
    limit: int = Query(500, ge=1, le=5000),
    sport: Optional[str] = Query(None),
    event_id: Optional[str] = Query(None),
):
    """
    Get latest odds for all or specific markets
    
    Args:
        limit: Max results (default 500)
        sport: Filter by sport
        event_id: Filter by event ID
    """
    try:
        session = SessionLocal()
        
        # Build query - get most recent odds per selection
        query = session.query(LiveOdds)
        
        if sport:
            query = query.filter(LiveOdds.sport == sport)
        if event_id:
            query = query.filter(LiveOdds.event_id == event_id)
        
        # Order by extraction time and limit
        odds = query.order_by(
            LiveOdds.extracted_at.desc(),
            LiveOdds.selection,
            LiveOdds.bookmaker
        ).limit(limit).all()
        
        session.close()
        
        return {
            "odds": [o.to_dict() for o in odds],
            "count": len(odds),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "odds": [],
            "count": 0,
            "last_updated": datetime.utcnow().isoformat()
        }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with documentation links"""
    return {
        "name": "EV_ARB Bot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ev_hits": "/api/ev/hits?limit=50&min_ev=0.01&sport=basketball_nba",
            "ev_summary": "/api/ev/summary",
            "odds_latest": "/api/odds/latest?limit=500&sport=basketball_nba",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
