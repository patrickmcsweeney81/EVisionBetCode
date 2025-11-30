"""BallDontLie enrichment module (optional).

Provides lightweight NBA player context to supplement EV player prop evaluation.
Activated only if environment variable BALLDONTLIE_ENABLED=1.

Data fetched (single on-demand call per player):
- Season averages (baseline performance & minutes)
- Recent games (last N, default 3) for minutes & points trend

We deliberately keep logic minimal to avoid performance overhead.
"""
from __future__ import annotations

import os
import time
from typing import Dict, Optional, Any, List

import requests

BASE = "https://www.balldontlie.io/api/v1"


def _get(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _minutes_trend(minutes: List[float]) -> str:
    if len(minutes) < 2:
        return "UNKNOWN"
    prev_avg = sum(minutes[:-1]) / max(1, len(minutes) - 1)
    last = minutes[-1]
    if last >= prev_avg + 3:
        return "RISING"
    if last <= prev_avg - 5:
        return "LOW"
    return "STABLE"


def fetch_player_context(player_name: str, recent_games: int = 3) -> Optional[Dict[str, Any]]:
    players = _get(f"{BASE}/players", {"search": player_name})
    if not players or not players.get("data"):
        return None
    player = players["data"][0]
    pid = player.get("id")
    if pid is None:
        return None

    season_avgs = _get(f"{BASE}/season_averages", {"player_ids[]": pid}) or {}
    season_list = season_avgs.get("data") or []
    season_avg = season_list[0] if season_list else {}

    stats = _get(f"{BASE}/stats", {"player_ids[]": pid, "per_page": recent_games}) or {}
    stat_rows = stats.get("data") or []
    recent = []
    min_vals: List[float] = []
    pts_vals: List[int] = []
    for row in stat_rows:
        game = row.get("game", {})
        date = (game.get("date") or "")[:10]
        min_raw = row.get("min")
        try:
            mins = float(min_raw) if min_raw not in (None, "", "0") else 0.0
        except Exception:
            mins = 0.0
        pts = row.get("pts") or 0
        reb = row.get("reb") or 0
        ast = row.get("ast") or 0
        recent.append({"date": date, "min": mins, "pts": pts, "reb": reb, "ast": ast})
        min_vals.append(mins)
        pts_vals.append(pts)

    form_pts_avg = round(sum(pts_vals) / len(pts_vals), 2) if pts_vals else None
    stability = _minutes_trend(min_vals) if min_vals else "UNKNOWN"

    return {
        "player_id": pid,
        "season_avg": season_avg,
        "recent_games": recent,
        "recent_form_pts_avg": form_pts_avg,
        "minutes_stability": stability,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
    }


def fetch_player_context_if_enabled(player_name: str) -> Optional[Dict[str, Any]]:
    if os.getenv("BALLDONTLIE_ENABLED", "0") != "1":
        return None
    return fetch_player_context(player_name)
