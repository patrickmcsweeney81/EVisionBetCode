"""Utility: list The Odds API sport keys.

Usage:
  C:/EVisionWorkspace/EVisionBetCode/.venv/Scripts/python.exe check_odds_api_sports.py

Reads ODDS_API_KEY from environment or from EVisionBetCode/.env.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> int:
    repo_dir = Path(__file__).resolve().parent
    _load_dotenv(repo_dir / ".env")

    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        print("ERROR: ODDS_API_KEY not found in env or .env")
        return 2

    url = "https://api.the-odds-api.com/v4/sports"
    resp = requests.get(url, params={"apiKey": api_key}, timeout=30)

    print(f"status: {resp.status_code}")
    print(f"requests remaining: {resp.headers.get('x-requests-remaining', 'N/A')}")

    try:
        resp.raise_for_status()
    except Exception:
        print(resp.text[:2000])
        raise

    data = resp.json()

    soccer = [s for s in data if str(s.get("key", "")).startswith("soccer_")]
    tennis = [s for s in data if str(s.get("key", "")).startswith("tennis_")]

    aussierules = [
        s for s in data if str(s.get("key", "")).startswith("aussierules_")
    ]
    rugbyleague = [
        s for s in data if str(s.get("key", "")).startswith("rugbyleague_")
    ]
    print("\nSoccer keys:")
    for s in soccer:
        print(f"- {s['key']}: {s.get('title','')}")

    print("\nTennis keys:")
    for s in tennis:
        print(f"- {s['key']}: {s.get('title','')}")

    print("\nAussie Rules keys:")
    for s in aussierules:
        print(f"- {s['key']}: {s.get('title','')}")

    print("\nRugby League keys:")
    for s in rugbyleague:
        print(f"- {s['key']}: {s.get('title','')}")

    common = [
        "soccer_epl",
        "soccer_uefa_champs_league",
        "tennis_atp",
        "tennis_wta",
        "aussierules_afl",
        "rugbyleague_nrl",
    ]
    present = {
        s.get("key"): s.get("title", "")
        for s in data
        if s.get("key") in common
    }

    print("\nCommon keys present:")
    for k in common:
        if k in present:
            print(f"- {k}: {present[k]}")
        else:
            print(f"- {k}: (not returned by /v4/sports)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
