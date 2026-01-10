import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Reuse the pipeline's constants and functions for parity
sys.path.append(str(Path(__file__).resolve().parents[1]))
import calculate_nba_ev_full as ev  # noqa: E402

EV_FILES = [
    Path('data/v3/extracts/basketball_nba_ev_full.csv'),
    Path('data/v3/extracts/basketball_nba_ev_full_new.csv'),
]


def latest_ev_csv() -> Path:
    for p in EV_FILES:
        if p.exists():
            return p
    raise FileNotFoundError("No EV CSV found. Run calculate_nba_ev_full.py first.")


def load_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Numeric helpers
    def parse_ev(evstr: str) -> float:
        try:
            if isinstance(evstr, str) and evstr.endswith('%'):
                return float(evstr[:-1])
            return float(evstr)
        except Exception:
            return np.nan

    def parse_dollar(od: str) -> float:
        try:
            if isinstance(od, str) and od.startswith('$'):
                return float(od[1:])
            return float(od)
        except Exception:
            return np.nan

    df['ev_num'] = df['EV'].apply(parse_ev) if 'EV' in df.columns else np.nan
    df['best_odds_num'] = df['Best book odds'].apply(parse_dollar) if 'Best book odds' in df.columns else np.nan
    return df


def build_pair_lookup(df: pd.DataFrame):
    pairs = {}
    if 'pair_id' not in df.columns:
        return pairs
    for i, row in df.iterrows():
        pid = row.get('pair_id')
        if pd.notna(pid):
            pairs.setdefault(pid, []).append(i)
    return pairs


def compute_devig_breakdown(df: pd.DataFrame, idx: int) -> pd.DataFrame:
    row = df.loc[idx]
    pid = row.get('pair_id')
    # Find opposite row by pair_id only (as the pipeline does)
    pairs = build_pair_lookup(df)
    if pd.isna(pid) or pid not in pairs or len(pairs[pid]) != 2:
        return pd.DataFrame()
    other_idx = [j for j in pairs[pid] if j != idx][0]
    other = df.loc[other_idx]

    records = []
    for book in ev.FAIR_ODDS_BOOKS:
        if book not in df.columns:
            continue
        o1 = row.get(book)
        o2 = other.get(book)
        if pd.isna(o1) or pd.isna(o2):
            continue
        # Adjust exchange
        if book == 'betfair_ex_eu':
            o1 = ev.remove_betfair_commission(o1, commission_rate=0.06)
            o2 = ev.remove_betfair_commission(o2, commission_rate=0.06)
        p1_raw = ev.odds_to_implied_prob(o1)
        p2_raw = ev.odds_to_implied_prob(o2)
        if pd.isna(p1_raw) or pd.isna(p2_raw):
            continue
        p1_devig, p2_devig = ev.devig_2way(p1_raw, p2_raw)
        if pd.isna(p1_devig):
            continue
        records.append({
            'book': book,
            'odds_this': o1,
            'odds_other': o2,
            'p1_raw': p1_raw,
            'p2_raw': p2_raw,
            'p1_devig': p1_devig,
            'weight': ev.BOOK_WEIGHTS.get(book, 1.0),
        })
    return pd.DataFrame.from_records(records)


def explain_row(df: pd.DataFrame, idx: int):
    row = df.loc[idx]
    print("Row summary:")
    cols = ['id','event_name','market_type','player_name','point','selection','best_au_bookmaker','Best book odds','Fair odds','EV','uses_devig','pair_id']
    present = [c for c in cols if c in df.columns]
    print(row[present].to_string())
    print()

    if row.get('uses_devig') is True and row.get('pair_id') is not None:
        br = compute_devig_breakdown(df, idx)
        if br.empty:
            print("No devig breakdown available (missing pair or odds)")
            return
        br['contrib'] = br['p1_devig'] * br['weight']
        total_w = br['weight'].sum()
        fair_prob = br['contrib'].sum() / total_w if total_w > 0 else np.nan
        fair_dec = 1.0 / fair_prob if fair_prob and fair_prob > 0 else np.nan

        print("Per-book devig + weights:")
        print(br.sort_values('weight', ascending=False)[['book','odds_this','odds_other','p1_raw','p2_raw','p1_devig','weight']].to_string(index=False))
        print()
        print(f"Weighted fair probability: {fair_prob:.4f}  -> fair odds: {fair_dec:.2f}")
        if 'Fair odds' in row:
            print(f"File fair odds: {row['Fair odds']}")
        print()
    else:
        # Single-outcome markets (no pair) – show which sharp books exist
        four_star = ['pinnacle','betfair_ex_eu','matchbook','draftkings','fanduel','lowvig']
        present = [b for b in four_star if b in df.columns and pd.notna(row.get(b))]
        print(f"4⭐ sharp books present on this line: {len(present)} -> {present}")
        print()


def main():
    ap = argparse.ArgumentParser(description='EV Inspector – explain fair odds & EV per row/pair')
    ap.add_argument('--csv', type=Path, default=None, help='Path to EV CSV (defaults to latest)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--id', type=int, help='Inspect by output id')
    g.add_argument('--pair-id', type=float, help='Inspect by pair_id')
    args = ap.parse_args()

    path = args.csv or latest_ev_csv()
    df = load_df(path)

    if args.id is not None:
        if 'id' not in df.columns:
            raise SystemExit('CSV missing id column')
        if args.id not in set(df['id']):
            raise SystemExit(f'id {args.id} not found in {path}')
        idx = df.index[df['id'] == args.id][0]
        explain_row(df, idx)
        return

    if args.pair_id is not None:
        if 'pair_id' not in df.columns:
            raise SystemExit('CSV missing pair_id column')
        sub = df[df['pair_id'] == args.pair_id]
        if sub.empty:
            raise SystemExit(f'pair_id {args.pair_id} not found in {path}')
        print(f"Found {len(sub)} rows for pair_id {args.pair_id}\n")
        for idx in sub.index:
            explain_row(df, idx)


if __name__ == '__main__':
    main()
