# EV Bot: Product and Build Plan (Nov 2025)

This document outlines a pragmatic dual-track plan: keep the EV engine solid while we stand up a lightweight web experience tailored to Australian bookmakers.

## Objectives
- Deliver a usable MVP for AU users: clear EV table, fast filtering, and actionable info.
- Keep the core EV math trustworthy (Pinnacle + median + interpolation) and observable.
- Prepare a simple marketing presence to start learning from early users.

## Current backend status (from latest run)
- Totals: fairs on both sides (0 zero-fair rows in last sample).
- Spreads: fairs on both sides for most lines; a couple of AU-only lines have $0.00 fair due to no non-AU neighbors.
- H2H: fairs currently not built by design; CSV shows $0.00 Fair/Prob for H2H rows.
- EV hits: 0 on the sample run (expected given market and thresholds).

## MVP scope (4–7 days)
1) Engine hardening
- Bake defaults: INTERP_MAX_GAP=1.5, INTERP_MIN_SAMPLES=2
- Add zero-fair health checks by market (threshold alerts)
- Optional: nearest-neighbor carry for spreads with only one sharp neighbor (guarded, small gap only)

2) API (read-only)
- Endpoint: GET /api/odds (paged) -> all_odds-like rows
- Endpoint: GET /api/hits (paged) -> EV hits
- Filters: sport, market, minEV, bookmaker, event time window
- CORS enabled for the web client; no auth for MVP

3) Web UI (client)
- EV table with sticky header, column chooser, instant filter (min EV, market, bookmaker)
- Row click -> detail drawer (all books for that event/market/line)
- Mobile-first; AU bookmaker badges

4) Marketing page
- Landing page explaining value prop, screenshots, responsible gambling, and signup/interest form

## Phase 2 (1–2 weeks after MVP)
- Auth (email magic link), rate limiting, and user settings
- Saved filters and Telegram/Email notifications
- Nightly data-quality report: coverage of fairs by market, outlier counts, API health
- Simple subscription/payments plan (later)

## Non-goals for MVP
- Arbitrage reintroduction
- Complex calculators; deep bankroll tooling

## Technical choices
- API: Python FastAPI (simple to deploy; great docs); reuse env handling and logging
- UI: Next.js (React) with Tailwind for fast iteration; deploy on Vercel
- Hosting: API on Render/Fly.io; UI on Vercel

## Acceptance criteria
- API returns data in <300ms p50 for simple filters
- Web table loads first page in <2s on 4G, supports sorting/filtering without reload
- Zero-fair count: totals=0; spreads<=2% of rows (excluding AU-only cases)
- Crash-free runs for 24h; basic error logs captured

## Risks and mitigations
- Sparse sharp coverage on certain AU lines -> interpolation + nearest-neighbor carry (guarded)
- Odds API rate limits -> pagination + caching layer; backoff strategy
- Legal/compliance -> add disclaimers and responsible gambling links prominently

## Work plan (checklist)
- [ ] Bake interpolation defaults in `ev_arb_bot.py`
- [ ] Add data-quality check step and counters in logs
- [ ] Scaffold FastAPI with `/api/odds` from `data/all_odds.csv` (initially file-backed)
- [ ] Define JSON schema for odds row; align with CSV headers
- [ ] Create Next.js app skeleton; EV table page
- [ ] Deploy API and UI; wire CORS and environment vars
- [ ] Draft landing page copy and screenshots

## Notes
- AU books remain excluded from fair-building by design to avoid circularity with EV targeting.
- H2H fairs are intentionally blank for now to focus effort where spreads/totals provide richer edges.
