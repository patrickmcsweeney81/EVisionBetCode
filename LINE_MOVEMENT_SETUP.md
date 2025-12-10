# Line Movement & Prop Alert System - Setup Guide

**Date:** December 11, 2025  
**Status:** Ready for implementation  
**Purpose:** Track price changes between odds extractions and detect high-value prop opportunities

---

## Overview

This system automatically:
1. **Tracks Price Changes** - Compares each extraction with the previous one
2. **Detects Line Movements** - Flags significant price deltas
3. **Color-codes Movements** - GREEN (price down) / RED (price up)
4. **Identifies Prop Alerts** - Detects high-EV player prop opportunities
5. **Archives All Data** - Maintains complete price history for analysis

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ extraction_v2/extract_odds.py (Stage 1)                 │
│ - Fetches current odds from The Odds API                │
│ - Writes to raw_odds_pure.csv                           │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ Pipeline V2 - NEW: Line Movement & Prop Detection      │
│  - Loads previous raw_odds_pure.csv                     │
│  - Compares with current extraction                     │
│  - Detects price movements (GREEN/RED)                  │
│  - Extracts prop alerts                                 │
│  - Writes to: line_movements.csv & prop_alerts.csv      │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ Pipeline V2 - EV Calculation (Stage 2)                  │
│ - Calculates EV opportunities                           │
│ - Writes to ev_opportunities.csv                        │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ Database Write - Insert All Data                        │
│  - live_odds (current prices)                           │
│  - price_history (archive)                              │
│  - line_movements (price changes with GREEN/RED tags)   │
│  - prop_alerts (high-value props)                       │
│  - ev_opportunities (EV value bets)                     │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│ Frontend Dashboard (EVisionBetSite)                      │
│  - Line Movements Card (Green/Red alerts)               │
│  - Prop Alerts Card (High-value props)                  │
│  - Price History Chart (track movement over time)       │
│  - EV Opportunities Table                               │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### 1. **live_odds** (Current prices only)
```sql
id | extracted_at | sport | event_id | market | selection | bookmaker | odds
```
**Purpose:** Current odds snapshot (updated each extraction)

### 2. **price_history** (Complete archive)
```sql
id | extracted_at | sport | event_id | market | selection | bookmaker | odds | is_current
```
**Purpose:** Archive of every odds snapshot - enables line tracking over time

### 3. **line_movements** ⭐ (GREEN/RED alerts)
```sql
id | detected_at | sport | event_id | market | selection | bookmaker |
    old_odds | new_odds | price_change | price_change_percent |
    movement_type | movement_percent | is_significant | significance_level
```
**Movement Types:**
- **DOWN (Green)** - Price decreased (better odds for bettor) 📉
- **UP (Red)** - Price increased (worse odds for bettor) 📈
- **SAME** - No change

**Significance Levels:**
- **MAJOR** - >5% change
- **MODERATE** - 2-5% change
- **MINOR** - <2% change

### 4. **prop_alerts** (High-value props)
```sql
id | detected_at | sport | event_id | player_name | prop_market | prop_line |
    over_odds | under_odds | best_side | best_book | ev_percent |
    alert_type | severity | is_active | closed_at
```
**Alert Types:**
- **HIGH_EV** - EV >= 5%
- **LINE_MOVE** - Significant line movement on prop
- **SHARP_SIGNAL** - Multiple sharp books backing same side
- **NEW_PROP** - New prop market detected

**Severity:**
- **HIGH** - EV >= 5%
- **MEDIUM** - EV 3-5%
- **LOW** - EV 1-3%

---

## Implementation Steps

### Step 1: Create Enhanced Database Schema

```bash
# Option A: If using PostgreSQL on Render
# Copy SQL from create_tables_enhanced.sql to Render PostgreSQL console

# Option B: Locally (for testing)
psql -U postgres -d your_database -f create_tables_enhanced.sql
```

**Files:**
- `create_tables_enhanced.sql` - Complete schema with all 5 tables + indexes

---

### Step 2: Update extract_odds.py

**Add at end of main() to archive previous extraction:**

```python
# Before writing current odds, backup previous extraction
if RAW_CSV.exists():
    timestamp = datetime.now().isoformat().replace(':', '-')
    backup_path = DATA_DIR / f"raw_odds_previous_{timestamp}.csv"
    shutil.copy(RAW_CSV, backup_path)
    print(f"[OK] Backed up previous odds to {backup_path.name}")

# Write current odds (as usual)
write_raw_odds_csv(all_rows, RAW_CSV)
```

**Result:** Maintains both current and previous extraction for comparison

---

### Step 3: Create pipeline_v2/line_movement_detector.py

**Status:** ✅ Already created (file location: pipeline_v2/line_movement_detector.py)

This module provides:
- `LineMovementDetector` - Compares odds and flags price changes
- `PropAlertDetector` - Extracts high-value prop opportunities

---

### Step 4: Integrate Line Movement Detection into calculate_opportunities.py

**Add to calculate_opportunities.py (after EV calculation):**

```python
from line_movement_detector import LineMovementDetector, PropAlertDetector

def main():
    # ... existing EV calculation ...
    
    # Stage 2B: Detect line movements
    print("\n" + "="*70)
    print("STAGE 2B: DETECTING LINE MOVEMENTS")
    print("="*70)
    
    # Load previous odds (from backup)
    previous_odds = None
    for backup in sorted(DATA_DIR.glob("raw_odds_previous_*.csv"), reverse=True):
        previous_odds = backup
        break
    
    if previous_odds:
        detector = LineMovementDetector(previous_odds, RAW_CSV)
        movements = detector.detect_movements()
        
        # Write results
        line_movements_csv = DATA_DIR / "line_movements.csv"
        detector.write_movements_csv(line_movements_csv)
        
        # Statistics
        green = len(detector.get_green_movements())
        red = len(detector.get_red_movements())
        significant = len(detector.filter_significant())
        
        print(f"\n[OK] Line Movements Detected:")
        print(f"  GREEN (price down): {green}")
        print(f"  RED (price up): {red}")
        print(f"  Significant (>3%): {significant}")
    else:
        print("[!] No previous odds - skipping line movement detection")
    
    # Stage 2C: Detect prop alerts
    print("\n" + "="*70)
    print("STAGE 2C: DETECTING PROP ALERTS")
    print("="*70)
    
    prop_detector = PropAlertDetector()
    prop_alerts = prop_detector.detect_from_ev_opportunities(all_opportunities)
    
    prop_alerts_csv = DATA_DIR / "prop_alerts.csv"
    prop_detector.write_alerts_csv(prop_alerts_csv)
    
    high = len([a for a in prop_alerts if a.severity == 'HIGH'])
    medium = len([a for a in prop_alerts if a.severity == 'MEDIUM'])
    
    print(f"\n[OK] Prop Alerts Detected:")
    print(f"  HIGH severity: {high}")
    print(f"  MEDIUM severity: {medium}")
```

---

### Step 5: Write Data to Database

**Add database inserts to calculate_opportunities.py:**

```python
def write_line_movements_to_db(session, movements_csv):
    """Insert line movements into PostgreSQL"""
    if not movements_csv.exists():
        return
    
    try:
        with open(movements_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                movement = LineMovement(
                    sport=row['sport'],
                    event_id=row['event_id'],
                    market=row['market'],
                    point=float(row.get('point') or 0) or None,
                    selection=row['selection'],
                    player_name=row.get('player_name'),
                    bookmaker=row['bookmaker'],
                    old_odds=float(row.get('old_odds') or 0) or None,
                    new_odds=float(row['new_odds']),
                    price_change=float(row.get('price_change', 0)),
                    price_change_percent=float(row.get('price_change_percent', 0)),
                    movement_type=row['movement_type'],
                    movement_percent=float(row.get('movement_percent', 0)),
                    is_significant=row.get('is_significant') == 'True',
                    significance_level=row['significance_level'],
                )
                session.add(movement)
        
        session.commit()
        print(f"[OK] Inserted line movements into database")
    except Exception as e:
        print(f"[!] Error inserting movements: {e}")

def write_prop_alerts_to_db(session, alerts_csv):
    """Insert prop alerts into PostgreSQL"""
    if not alerts_csv.exists():
        return
    
    try:
        with open(alerts_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alert = PropAlert(
                    sport=row['sport'],
                    event_id=row['event_id'],
                    player_name=row['player_name'],
                    prop_market=row['prop_market'],
                    prop_line=float(row.get('prop_line') or 0) or None,
                    over_odds=float(row.get('over_odds') or 0) or None,
                    under_odds=float(row.get('under_odds') or 0) or None,
                    best_side=row.get('best_side', 'UNKNOWN'),
                    best_book=row.get('best_book', ''),
                    ev_percent=float(row.get('ev_percent', 0)),
                    alert_type='HIGH_EV',
                    severity=row['severity'],
                )
                session.add(alert)
        
        session.commit()
        print(f"[OK] Inserted prop alerts into database")
    except Exception as e:
        print(f"[!] Error inserting alerts: {e}")
```

---

### Step 6: Create API Endpoints in backend_api.py

```python
@app.get("/api/line-movements")
async def get_line_movements(
    sport: Optional[str] = None,
    movement_type: Optional[str] = None,  # 'UP', 'DOWN'
    significant_only: bool = False,
    limit: int = 100
):
    """Get recent line movements (price changes)"""
    session = SessionLocal()
    try:
        query = session.query(LineMovement).order_by(LineMovement.detected_at.desc())
        
        if sport:
            query = query.filter(LineMovement.sport == sport)
        if movement_type:
            query = query.filter(LineMovement.movement_type == movement_type)
        if significant_only:
            query = query.filter(LineMovement.is_significant == True)
        
        movements = query.limit(limit).all()
        return {
            "total": len(movements),
            "data": [m.to_dict() for m in movements]
        }
    finally:
        session.close()

@app.get("/api/prop-alerts")
async def get_prop_alerts(
    sport: Optional[str] = None,
    severity: Optional[str] = None,  # 'HIGH', 'MEDIUM', 'LOW'
    active_only: bool = True,
    limit: int = 100
):
    """Get prop alerts (high-value player prop opportunities)"""
    session = SessionLocal()
    try:
        query = session.query(PropAlert).order_by(PropAlert.detected_at.desc())
        
        if sport:
            query = query.filter(PropAlert.sport == sport)
        if severity:
            query = query.filter(PropAlert.severity == severity)
        if active_only:
            query = query.filter(PropAlert.is_active == True)
        
        alerts = query.limit(limit).all()
        return {
            "total": len(alerts),
            "data": [a.to_dict() for a in alerts]
        }
    finally:
        session.close()
```

---

## Frontend Card Components

### Line Movements Card
```jsx
<Card title="Line Movements">
  <LineMovementTable>
    {/* Display with color coding */}
    {movements.map(m => (
      <Row key={m.id} color={m.movement_type === 'DOWN' ? 'green' : 'red'}>
        <Cell>{m.bookmaker}</Cell>
        <Cell>{m.old_odds} → {m.new_odds}</Cell>
        <Cell>{m.movement_percent}%</Cell>
      </Row>
    ))}
  </LineMovementTable>
</Card>
```

### Prop Alerts Card
```jsx
<Card title="Prop Alerts">
  <PropAlertTable>
    {/* Filter by severity */}
    {propAlerts.map(a => (
      <Row key={a.id} severity={a.severity}>
        <Cell>{a.player_name}</Cell>
        <Cell>{a.prop_market}</Cell>
        <Cell className={a.best_side === 'OVER' ? 'highlight'}>
          {a.best_side} {a.prop_line}
        </Cell>
        <Cell>{a.ev_percent}%</Cell>
      </Row>
    ))}
  </PropAlertTable>
</Card>
```

---

## Running the System

### Local Testing

```bash
# 1. Extract odds
python pipeline_v2/extract_odds.py
# Output: raw_odds_pure.csv

# 2. Calculate EV + detect movements + detect props
python pipeline_v2/calculate_opportunities.py
# Outputs:
# - ev_opportunities.csv
# - line_movements.csv (NEW)
# - prop_alerts.csv (NEW)
```

### Render Deployment

The cron jobs automatically run:

1. **extract_odds.py** (every 30 min)
   - Fetches latest odds
   - Creates raw_odds_pure.csv
   - Backs up previous extraction

2. **calculate_opportunities.py** (runs after extract)
   - Compares old vs new odds → line_movements.csv
   - Extracts props → prop_alerts.csv
   - Calculates EV → ev_opportunities.csv
   - Writes all to PostgreSQL

---

## Output Files

### line_movements.csv
```
detected_at,sport,event_id,market,selection,bookmaker,old_odds,new_odds,price_change,movement_type,significance_level
2025-12-11T10:30:00,nba,event123,h2h,Boston Celtics,Sportsbet,1.95,1.92,-0.03,DOWN,MODERATE
2025-12-11T10:30:00,nba,event456,totals_o,Over 215.5,Pointsbet,1.90,1.95,0.05,UP,MODERATE
```

### prop_alerts.csv
```
detected_at,sport,event_id,player_name,prop_market,prop_line,over_odds,under_odds,best_side,ev_percent,severity
2025-12-11T10:35:00,nba,event789,LeBron James,player_points,28.5,1.91,1.91,OVER,5.2,HIGH
2025-12-11T10:35:00,nba,event789,LeBron James,player_assists,6.5,1.85,2.05,UNDER,4.1,MEDIUM
```

---

## Success Indicators

✅ Line movements detected and color-coded (GREEN/RED)  
✅ Prop alerts identified by severity  
✅ Data written to both CSV and database  
✅ API endpoints return movement and alert data  
✅ Frontend cards display real-time information  
✅ Price history archive grows with each extraction

---

## Next Steps

1. **Deploy to Render:**
   - Update cron job build commands to run enhanced pipeline
   - Create tables using enhanced SQL schema
   - Test with manual cron run

2. **Build Frontend Cards:**
   - LineMovements component with GREEN/RED color coding
   - PropAlerts component with severity badges
   - Charts for price history over time

3. **Add Notifications (Optional):**
   - Email/SMS on HIGH severity props
   - Alert on MAJOR line movements
   - Daily summary of opportunities

---

## Files Created/Modified

- ✅ `create_tables_enhanced.sql` - Complete schema
- ✅ `backend_api.py` - Added PriceHistory, LineMovement, PropAlert models + API endpoints
- ✅ `pipeline_v2/line_movement_detector.py` - Detection logic
- ✅ This setup guide

---

**Ready to deploy!** 🚀
