"""
FastAPI backend service for EV_ARB Bot
Exposes PostgreSQL data to frontend via REST API
Runs on Render as a Web Service (not cron job)
"""

import csv
import hashlib
import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import (
    Column,
    DateTime,
    Boolean,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Try to load v3 config system (weights, sports config, etc.)
try:
    from src.v3.configs import get_sport_config, get_enabled_sports
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Load environment variables
load_dotenv()


# Locate data directory (mirrors pipeline get_data_dir)
def get_data_dir():
    """Find data directory â€“ works locally and on Render."""
    cwd = Path.cwd()
    # Normalize duplicate /src/src patterns
    cwd_str = str(cwd).replace("\\src\\src", "\\src").replace("/src/src", "/src")
    cwd = Path(cwd_str)

    # Priority 1: cwd/data
    data_path = cwd / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    if data_path.exists() and data_path.is_dir():
        return data_path

    # Priority 2: parent/data if cwd is /src
    if cwd.name == "src":
        data_path = cwd.parent / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        if data_path.exists() and data_path.is_dir():
            return data_path

    # Priority 3: script parent (backend_api at repo root)
    script_parent = Path(__file__).parent
    data_path = script_parent / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    if data_path.exists() and data_path.is_dir():
        return data_path

    # Fallback
    return cwd / "data"


DATA_DIR = get_data_dir()
EV_CSV = DATA_DIR / "ev_hits.csv"
RAW_CSV = DATA_DIR / "raw_odds_pure.csv"

# ============================================================================
# ADMIN CREDENTIALS (from env or hardcoded for simplicity)
# ============================================================================

ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    hashlib.sha256("admin123".encode()).hexdigest(),  # Default: hashed "admin123"
)


def verify_admin_password(password: str) -> bool:
    """Verify admin password"""
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH


# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("âš ï¸  DATABASE_URL not set - running in CSV-only mode (no database)")
    engine = None
else:
    # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    try:
        engine = create_engine(DATABASE_URL, echo=False)
    except Exception as e:
        print(f"âš ï¸  Database connection error: {e}")
        print("âš ï¸  Starting app without database - API will serve CSV only")
        engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
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
            # Aliases for backward compatibility with frontend
            "bookmaker": self.best_book,
            "odds_decimal": round(self.best_odds, 2) if self.best_odds else None,
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
            "price_change_percent": (
                round(self.price_change_percent, 2) if self.price_change_percent else None
            ),
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
    version="2.0",
)

# Enable CORS for frontend communication
origins = [
    "http://localhost:3000",  # Local React dev
    "http://localhost:3001",  # Local React dev (alternate port)
    "http://localhost:5173",  # Vite dev server
    "http://localhost:8000",  # Backend self (for direct testing)
    "http://localhost:62527",  # npx serve production build
    "http://127.0.0.1:3000",  # Localhost via IP
    "http://127.0.0.1:3001",  # Localhost via IP (alternate port)
    "http://127.0.0.1:5173",  # Vite via IP
    "http://127.0.0.1:8000",  # Backend self via IP
    "https://evisionbet.com",
    "https://www.evisionbet.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Render with pipeline status."""
    health_data = {
        "status": "healthy",
        "version": "2.0",
        "database": "connected" if os.getenv("DATABASE_URL") else "csv_fallback",
        "pipelines": {}
    }
    
    # Check if CSV files exist and get their last modified times
    if EV_CSV.exists():
        ev_mtime = datetime.fromtimestamp(EV_CSV.stat().st_mtime)
        health_data["pipelines"]["calculate_ev"] = {
            "status": "healthy",
            "last_run": ev_mtime.isoformat(),
            "age_seconds": (datetime.now() - ev_mtime).total_seconds()
        }
    else:
        health_data["pipelines"]["calculate_ev"] = {
            "status": "missing",
            "last_run": None,
            "age_seconds": None
        }
    
    if RAW_CSV.exists():
        raw_mtime = datetime.fromtimestamp(RAW_CSV.stat().st_mtime)
        health_data["pipelines"]["extract_odds"] = {
            "status": "healthy",
            "last_run": raw_mtime.isoformat(),
            "age_seconds": (datetime.now() - raw_mtime).total_seconds()
        }
    else:
        health_data["pipelines"]["extract_odds"] = {
            "status": "missing",
            "last_run": None,
            "age_seconds": None
        }
    
    return health_data


@app.get("/")
async def root_endpoint():  # Renamed from 'root' to avoid redefinition
    """Root endpoint."""
    return {"message": "EV_ARB API v2.0", "docs": "/docs"}


# ============================================================================
# EV HITS ENDPOINTS
# ============================================================================


@app.get("/api/ev/hits")
async def get_ev_hits(
    limit: int = Query(50, ge=1, le=5000),
    offset: int = Query(0, ge=0),
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

    def csv_fallback():
        # Read from ev_hits.csv when database is unavailable or empty
        if not EV_CSV.exists():
            return [], 0

        def first(row, keys):
            for k in keys:
                if k in row and row.get(k) not in (None, ""):
                    return row.get(k)
            return None

        def parse_float(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            s = str(val).strip()
            if s == "":
                return None
            # Remove common adornments
            s_raw = s
            s = s.replace("%", "").replace("$", "")
            try:
                num = float(s)
                # If original had % and value likely in percent, convert to decimal
                if "%" in s_raw:
                    return num / 100.0
                return num
            except Exception:
                return None

        def parse_percent(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                # Heuristic: if >= 1.0 assume already decimal? Keep as-is
                return float(val) if float(val) <= 1.0 else float(val) / 100.0
            s = str(val).strip()
            if s == "":
                return None
            if s.endswith("%"):
                try:
                    return float(s[:-1]) / 100.0
                except Exception:
                    return None
            try:
                num = float(s)
                return num if num <= 1.0 else num / 100.0
            except Exception:
                return None

        rows = []
        with EV_CSV.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Support both internal headers and display headers
                    sport_val = first(row, ["sport", "Sport"]) or ""
                    if sport and sport_val and sport_val != sport:
                        continue

                    teams = first(row, ["teams", "Teams"]) or ""
                    away_team_val, home_team_val = None, None
                    if " V " in teams:
                        parts = teams.split(" V ", 1)
                        away_team_val = parts[0].strip()
                        home_team_val = parts[1].strip()
                    else:
                        away_team_val = first(row, ["away_team", "Away Team"]) or None
                        home_team_val = first(row, ["home_team", "Home Team"]) or None

                    ev_val = parse_percent(first(row, ["ev_percent", "EV%", "ev%", "ev"])) or 0.0
                    if ev_val < min_ev:
                        continue

                    best_book_val = first(row, ["best_book", "Book", "bookmaker"]) or ""
                    best_odds_val = parse_float(first(row, ["best_odds", "odds_decimal", "Odds"]))
                    fair_val = parse_float(first(row, ["fair_odds", "Fair"]))
                    prob_val = parse_percent(first(row, ["implied_prob", "Prob"]))
                    stake_val = parse_float(first(row, ["stake", "Stake"]))
                    sharps_val = parse_float(first(row, ["sharp_book_count", "Sharps"])) or 0
                    line_val = parse_float(first(row, ["point", "Line"]))

                    rows.append(
                        {
                            "sport": sport_val,
                            "event_id": first(row, ["event_id", "Event ID"]) or None,
                            "away_team": away_team_val,
                            "home_team": home_team_val,
                            "commence_time": first(row, ["commence_time", "Start Time"]) or None,
                            "market": first(row, ["market", "Market"]) or None,
                            "point": line_val,
                            "selection": first(row, ["selection", "Selection"]) or None,
                            "player": first(row, ["player", "Player"]) or None,
                            "fair_odds": fair_val,
                            "best_book": best_book_val,
                            "best_odds": best_odds_val,
                            "ev_percent": ev_val,
                            "sharp_book_count": int(sharps_val or 0),
                            "implied_prob": prob_val,
                            "stake": stake_val,
                            "kelly_fraction": parse_float(first(row, ["kelly_fraction"])) or None,
                            "detected_at": first(row, ["detected_at"]) or None,
                            "created_at": first(row, ["created_at"]) or None,
                            # Aliases for frontend convenience
                            "bookmaker": best_book_val,
                            "odds_decimal": best_odds_val,
                        }
                    )
                except Exception:
                    continue
        # Sort by ev_percent desc and apply offset/limit
        rows = sorted(rows, key=lambda r: r.get("ev_percent", 0), reverse=True)
        total = len(rows)
        rows = rows[offset : offset + limit]
        return rows, total

    try:
        # If no database session available, use CSV directly
        if not SessionLocal:
            hits, total_count = csv_fallback()
            last_updated = None
            if hits:
                timestamps = [
                    h.get("detected_at") or h.get("created_at")
                    for h in hits
                    if h.get("detected_at") or h.get("created_at")
                ]
                if timestamps:
                    last_updated = max(timestamps)
            return {
                "hits": hits,
                "count": len(hits),
                "total_count": total_count,
                "last_updated": last_updated or datetime.utcnow().isoformat(),
                "filters": {"limit": limit, "offset": offset, "min_ev": min_ev, "sport": sport},
            }

        session = SessionLocal()

        # Build query
        query = session.query(EVOpportunity).filter(EVOpportunity.ev_percent >= min_ev)

        # Apply sport filter if provided
        if sport:
            query = query.filter(EVOpportunity.sport == sport)

        # Order by EV descending, limit results
        hits = query.order_by(EVOpportunity.ev_percent.desc()).offset(offset).limit(limit).all()

        # If database empty, fallback to CSV
        if not hits:
            session.close()
            hits_csv, total_count = csv_fallback()
            last_updated = None
            if hits_csv:
                timestamps = [
                    h.get("detected_at") or h.get("created_at")
                    for h in hits_csv
                    if h.get("detected_at") or h.get("created_at")
                ]
                if timestamps:
                    last_updated = max(timestamps)
            return {
                "hits": hits_csv,
                "count": len(hits_csv),
                "total_count": total_count,
                "last_updated": last_updated or datetime.utcnow().isoformat(),
                "filters": {"limit": limit, "offset": offset, "min_ev": min_ev, "sport": sport},
            }

        # Get summary stats (still in DB path; optional)
        all_hits = session.query(EVOpportunity).all()
        session.close()

        last_updated = None
        if hits:
            last_updated = max((h.detected_at or h.created_at) for h in hits).isoformat()

        return {
            "hits": [h.to_dict() for h in hits],
            "count": len(hits),
            "total_count": len(all_hits),
            "last_updated": last_updated or datetime.utcnow().isoformat(),
            "filters": {"limit": limit, "offset": offset, "min_ev": min_ev, "sport": sport},
        }

    except Exception as e:
        # Fallback to CSV if database query fails for any reason
        try:
            hits_csv, total_count = csv_fallback()
            last_updated = None
            if hits_csv:
                timestamps = [
                    h.get("detected_at") or h.get("created_at")
                    for h in hits_csv
                    if h.get("detected_at") or h.get("created_at")
                ]
                if timestamps:
                    last_updated = max(timestamps)
            return {
                "hits": hits_csv,
                "count": len(hits_csv),
                "total_count": total_count,
                "last_updated": last_updated or datetime.utcnow().isoformat(),
                "filters": {"limit": limit, "offset": offset, "min_ev": min_ev, "sport": sport},
                "warning": f"db_error_fallback: {str(e)}",
            }
        except Exception:
            return {
                "error": str(e),
                "hits": [],
                "count": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }


@app.get("/api/ev/summary")
async def get_ev_summary():
    """Get summary stats about EV opportunities"""
    try:
        if not SessionLocal:
            if not EV_CSV.exists():
                return {
                    "available": False,
                    "total_hits": 0,
                    "top_ev": 0,
                    "sports": {},
                    "last_updated": datetime.utcnow().isoformat(),
                }

            rows = []
            with EV_CSV.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        ev_val = float(row.get("ev_percent", 0))
                        rows.append(row | {"ev_percent": ev_val})
                    except Exception:
                        continue

            if not rows:
                return {
                    "available": False,
                    "total_hits": 0,
                    "top_ev": 0,
                    "sports": {},
                    "last_updated": datetime.utcnow().isoformat(),
                }

            sports_dict = {}
            top_ev = 0
            timestamps = []

            for hit in rows:
                sport_val = hit.get("sport")
                if sport_val not in sports_dict:
                    sports_dict[sport_val] = 0
                sports_dict[sport_val] += 1

                if hit.get("ev_percent", 0) > top_ev:
                    top_ev = hit.get("ev_percent", 0)

                ts = hit.get("detected_at") or hit.get("created_at")
                if ts:
                    timestamps.append(ts)

            last_updated = max(timestamps) if timestamps else datetime.utcnow().isoformat()

            return {
                "available": True,
                "total_hits": len(rows),
                "top_ev": round(top_ev, 2),
                "sports": sports_dict,
                "last_updated": last_updated,
            }

        session = SessionLocal()

        # Query all EV opportunities
        all_hits = session.query(EVOpportunity).all()

        if not all_hits:
            return {
                "available": False,
                "total_hits": 0,
                "top_ev": 0,
                "sports": {},
                "last_updated": datetime.utcnow().isoformat(),
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
            "last_updated": last_updated,
        }

    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "total_hits": 0,
            "top_ev": 0,
            "sports": {},
            "last_updated": datetime.utcnow().isoformat(),
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
        if not SessionLocal:
            return {
                "error": "database_not_configured",
                "odds": [],
                "count": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

        session = SessionLocal()

        # Build query - get most recent odds per selection
        query = session.query(LiveOdds)

        if sport:
            query = query.filter(LiveOdds.sport == sport)
        if event_id:
            query = query.filter(LiveOdds.event_id == event_id)

        # Order by extraction time and limit
        odds = (
            query.order_by(LiveOdds.extracted_at.desc(), LiveOdds.selection, LiveOdds.bookmaker)
            .limit(limit)
            .all()
        )

        session.close()

        return {
            "odds": [o.to_dict() for o in odds],
            "count": len(odds),
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "error": str(e),
            "odds": [],
            "count": 0,
            "last_updated": datetime.utcnow().isoformat(),
        }


@app.get("/api/odds/raw")
async def get_raw_odds(
    limit: int = Query(500, ge=1, le=20000),
    offset: int = Query(0, ge=0),
    sport: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
):
    """
    Serve raw odds directly from raw_odds_pure.csv for frontend display when DB is unavailable.
    """
    if not RAW_CSV.exists():
        return {
            "rows": [],
            "count": 0,
            "last_updated": datetime.utcnow().isoformat(),
            "columns": [],
            "error": "raw_csv_not_found",
        }

    def parse_float(val):
        if val is None:
            return None
        try:
            return float(val)
        except Exception:
            try:
                s = str(val).strip()
                if s == "":
                    return None
                return float(s)
            except Exception:
                return None

    rows = []
    row_index = 0  # Track which row we're on (for offset calculation)
    total_count = 0
    columns = []
    last_ts = None

    try:
        with RAW_CSV.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []
            for row in reader:
                if sport and row.get("sport") != sport:
                    continue
                if market and row.get("market") != market:
                    continue

                total_count += 1
                row_index += 1

                # Capture timestamp before processing (use either timestamp or commence_time)
                ts_val = row.get("timestamp") or row.get("commence_time")
                if ts_val:
                    last_ts = ts_val

                # Only include rows after the offset point
                if row_index <= offset:
                    continue

                # Keep as-is but coerce numeric bookmaker columns to float where possible
                clean_row = {}
                for k, v in row.items():
                    if k in [
                        "timestamp",
                        "sport",
                        "event_id",
                        "away_team",
                        "home_team",
                        "commence_time",
                        "market",
                        "point",
                        "selection",
                    ]:
                        clean_row[k] = v
                    else:
                        clean_row[k] = parse_float(v)

                rows.append(clean_row)

                # Stop when we have enough rows
                if len(rows) >= limit:
                    break

    except Exception as e:
        return {
            "rows": [],
            "count": 0,
            "total_count": 0,
            "columns": [],
            "error": f"Failed to read raw odds CSV: {str(e)}",
            "last_updated": datetime.utcnow().isoformat(),
        }

    return {
        "rows": rows,
        "count": len(rows),
        "total_count": total_count,
        "columns": columns,
        "last_updated": last_ts or datetime.utcnow().isoformat(),
    }


# ============================================================================
# ADMIN ENDPOINTS (Auth-protected CSV download & database view)
# ============================================================================


@app.post("/api/admin/auth")
async def admin_auth(password: str = Query(...)):
    """
    Authenticate as admin

    Args:
        password: Admin password

    Returns:
        {"authenticated": true/false, "token": "..."}
    """
    if verify_admin_password(password):
        # Generate simple token (in production, use JWT)
        token = hashlib.sha256((password + datetime.utcnow().isoformat()).encode()).hexdigest()
        return {"authenticated": True, "token": token, "expires_in": 3600}  # 1 hour
    else:
        raise HTTPException(status_code=401, detail="Invalid password")


@app.get("/api/admin/ev-opportunities-csv")
async def download_ev_csv(authorization: Optional[str] = Header(None)):
    """
    Download EV opportunities as CSV from database
    Admin/designer only access

    Args:
        authorization: Bearer token from admin auth

    Returns:
        CSV file stream
    """
    # Simple token validation (in production, use JWT verification)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized - missing token")

    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured (CSV-only mode)")

    try:
        session = SessionLocal()

        # Query all EV opportunities
        opportunities = session.query(EVOpportunity).order_by(EVOpportunity.ev_percent.desc()).all()

        if not opportunities:
            return StreamingResponse(
                iter([b"No opportunities found\n"]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=ev_hits.csv"},
            )

        # Build CSV in memory
        output = StringIO()

        # Headers
        headers = [
            "sport",
            "event_id",
            "away_team",
            "home_team",
            "commence_time",
            "market",
            "point",
            "selection",
            "player",
            "fair_odds",
            "best_odds",
            "best_book",
            "ev_percent",
            "sharp_book_count",
            "implied_prob",
            "stake",
            "kelly_fraction",
            "detected_at",
        ]

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        # Format and write rows
        for opp in opportunities:
            row = {
                "sport": opp.sport,
                "event_id": opp.event_id,
                "away_team": opp.away_team or "",
                "home_team": opp.home_team or "",
                "commence_time": opp.commence_time.isoformat() if opp.commence_time else "",
                "market": opp.market,
                "point": f"{opp.point:.1f}" if opp.point else "",
                "selection": opp.selection,
                "player": opp.player or "",
                "fair_odds": f"{opp.fair_odds:.4f}" if opp.fair_odds else "",
                "best_odds": f"{opp.best_odds:.4f}" if opp.best_odds else "",
                "best_book": opp.best_book,
                "ev_percent": f"{opp.ev_percent:.2f}%",
                "sharp_book_count": opp.sharp_book_count,
                "implied_prob": f"{opp.implied_prob:.2f}%" if opp.implied_prob else "",
                "stake": f"${int(opp.stake)}" if opp.stake else "",
                "kelly_fraction": f"{opp.kelly_fraction:.3f}" if opp.kelly_fraction else "",
                "detected_at": opp.detected_at.isoformat() if opp.detected_at else "",
            }
            writer.writerow(row)

        session.close()

        # Return as downloadable CSV
        csv_content = output.getvalue()

        async def iterfile():
            yield csv_content.encode()

        return StreamingResponse(
            iterfile(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ev_opportunities_download.csv"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")


@app.get("/api/admin/raw-odds-csv")
async def download_raw_odds_csv(authorization: Optional[str] = Header(None)):
    """
    Download raw odds as CSV from database
    Admin/designer only access

    Args:
        authorization: Bearer token from admin auth

    Returns:
        CSV file stream
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized - missing token")

    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured (CSV-only mode)")

    try:
        session = SessionLocal()

        # Get latest extraction timestamp
        latest = session.query(LiveOdds).order_by(LiveOdds.extracted_at.desc()).first()

        if not latest:
            return StreamingResponse(
                iter([b"No odds data found\n"]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=raw_odds.csv"},
            )

        latest_time = latest.extracted_at

        # Query odds from latest extraction
        odds = (
            session.query(LiveOdds)
            .filter(LiveOdds.extracted_at == latest_time)
            .order_by(LiveOdds.sport, LiveOdds.event_id, LiveOdds.market)
            .all()
        )

        # Build CSV in memory
        output = StringIO()

        headers = [
            "sport",
            "event_id",
            "commence_time",
            "market",
            "point",
            "selection",
            "bookmaker",
            "odds",
        ]

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        # Write rows
        for odd in odds:
            row = {
                "sport": odd.sport,
                "event_id": odd.event_id,
                "commence_time": odd.commence_time.isoformat() if odd.commence_time else "",
                "market": odd.market,
                "point": f"{odd.point:.1f}" if odd.point else "",
                "selection": odd.selection,
                "bookmaker": odd.bookmaker,
                "odds": f"{odd.odds:.4f}",
            }
            writer.writerow(row)

        session.close()

        # Return as downloadable CSV
        csv_content = output.getvalue()

        async def iterfile():
            yield csv_content.encode()

        return StreamingResponse(
            iterfile(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=raw_odds_{latest_time.isoformat().split('.')[0].replace(':', '-')}.csv"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")


@app.get("/api/admin/database-stats")
async def get_database_stats(authorization: Optional[str] = Header(None)):
    """
    Get database statistics - row counts and latest updates
    Admin/designer only

    Args:
        authorization: Bearer token from admin auth

    Returns:
        Statistics about database contents
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized - missing token")

    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured (CSV-only mode)")

    try:
        session = SessionLocal()

        # Count records
        ev_count = session.query(EVOpportunity).count()
        odds_count = session.query(LiveOdds).count()
        history_count = session.query(PriceHistory).count()

        # Get latest timestamps
        latest_ev = session.query(EVOpportunity).order_by(EVOpportunity.detected_at.desc()).first()

        latest_odds = session.query(LiveOdds).order_by(LiveOdds.extracted_at.desc()).first()

        session.close()

        return {
            "ev_opportunities": {
                "count": ev_count,
                "latest_update": latest_ev.detected_at.isoformat() if latest_ev else None,
            },
            "live_odds": {
                "count": odds_count,
                "latest_update": latest_odds.extracted_at.isoformat() if latest_odds else None,
            },
            "price_history": {"count": history_count},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================


@app.get("/api/config/weights")
async def get_config_weights():
    """
    Get EVisionBet weight configuration for all sports and bookmakers.
    Frontend uses this to recalculate EV with user-adjusted weights.
    
    Returns:
    {
        "sports": {
            "basketball_nba": {
                "weights": {
                    "pinnacle": 0.50,
                    "draftkings": 0.30,
                    "fanduel": 0.20,
                    ...
                }
            },
            ...
        },
        "timestamp": "2025-12-26T..."
    }
    
    Frontend adjusts weights with sliders (0-4 scale):
    - user_weight[book] = slider_value (0-4)
    - normalized_weight[book] = user_weight[book] / sum(all user_weights)
    - Then recalculates fair_odds using same formula as backend
    """
    try:
        if not CONFIG_AVAILABLE:
            return {
                "error": "Config system not available",
                "sports": {},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Build weight response for all enabled sports
        sports_weights = {}
        enabled_sports = get_enabled_sports()
        
        for sport_key in enabled_sports:
            try:
                sport_config = get_sport_config(sport_key)
                if sport_config and "evisionbet_weights" in sport_config:
                    sports_weights[sport_key] = {
                        "weights": sport_config["evisionbet_weights"],
                        "title": sport_config.get("title", sport_key),
                    }
            except Exception:
                # Skip sports with config errors
                continue
        
        return {
            "sports": sports_weights,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "These are EVisionBet's hidden weights. Frontend users start at 0 for all books and adjust via sliders.",
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "sports": {},
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/")
async def root():
    """API root endpoint with documentation links"""
    return {
        "name": "EV_ARB Bot API",
        "version": "2.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ev_hits": "/api/ev/hits?limit=50&min_ev=0.01&sport=basketball_nba",
            "ev_summary": "/api/ev/summary",
            "odds_latest": "/api/odds/latest?limit=500&sport=basketball_nba",
            "config_weights": "/api/config/weights",
            "admin_auth": "/api/admin/auth?password=YOUR_PASSWORD",
            "admin_ev_csv": "/api/admin/ev-opportunities-csv (requires Bearer token)",
            "admin_raw_odds_csv": "/api/admin/raw-odds-csv (requires Bearer token)",
            "admin_stats": "/api/admin/database-stats (requires Bearer token)",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

