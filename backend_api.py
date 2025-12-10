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
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    market = Column(String, nullable=False)
    selection = Column(String, nullable=False)
    bookmaker = Column(String, nullable=False)
    odds = Column(Float, nullable=False)
    extracted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "market": self.market,
            "selection": self.selection,
            "bookmaker": self.bookmaker,
            "odds": self.odds,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
        }


class EVOpportunity(Base):
    """EV opportunities above threshold"""
    __tablename__ = "ev_opportunities"
    
    id = Column(Integer, primary_key=True)
    sport = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    market = Column(String, nullable=False)
    selection = Column(String, nullable=False)
    fair_odds = Column(Float, nullable=False)
    best_odds = Column(Float, nullable=False)
    best_book = Column(String, nullable=False)
    ev_percent = Column(Float, nullable=False)
    sharp_book_count = Column(Integer, default=0)
    extracted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "market": self.market,
            "selection": self.selection,
            "fair_odds": round(self.fair_odds, 2),
            "best_odds": round(self.best_odds, 2),
            "best_book": self.best_book,
            "ev_percent": round(self.ev_percent * 100, 2),
            "sharp_book_count": self.sharp_book_count,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
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
            last_updated = max(h.extracted_at for h in hits).isoformat()
        
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
            if hit.ev_percent * 100 > top_ev:
                top_ev = hit.ev_percent * 100
        
        last_updated = max(h.extracted_at for h in all_hits).isoformat()
        
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
