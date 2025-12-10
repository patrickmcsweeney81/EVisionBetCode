# Line Movements & Prop Alerts - Frontend Implementation Guide

**Status:** System ready for frontend integration  
**Location:** Backend APIs at `/api/line-movements` and `/api/prop-alerts`

---

## Visual Design Reference

### Card 1: Line Movements (Price Changes)

#### Display Format
```
┌─────────────────────────────────────────────────┐
│ 📊 LINE MOVEMENTS - Last 30 Minutes              │
├─────────────────────────────────────────────────┤
│                                                  │
│ ✅ GREEN (Price Down - Better for Bettor)       │
│  ┌──────────────────────────────────────────┐  │
│  │ Bookmaker | Old Odds | New Odds | Change │  │
│  ├──────────────────────────────────────────┤  │
│  │ Sportsbet │  1.95   │  1.92   │ -1.5%  │  │
│  │ Pointsbet │  2.10   │  2.03   │ -3.3%  │  │
│  │ Tab       │  1.98   │  1.95   │ -1.5%  │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│ ❌ RED (Price Up - Worse for Bettor)            │
│  ┌──────────────────────────────────────────┐  │
│  │ Bookmaker | Old Odds | New Odds | Change │  │
│  ├──────────────────────────────────────────┤  │
│  │ Unibet    │  1.85   │  1.92   │ +3.8%  │  │
│  │ Ladbrokes │  2.05   │  2.12   │ +3.4%  │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│ 📈 MAJOR moves (>5% change)                    │
│  ┌──────────────────────────────────────────┐  │
│  │ Neds     │  1.90   │  2.00   │ +5.3%  │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### React Component
```jsx
import React from 'react';

function LineMovementsCard() {
  const [movements, setMovements] = React.useState([]);

  React.useEffect(() => {
    fetch('/api/line-movements?limit=50&significant_only=true')
      .then(r => r.json())
      .then(d => setMovements(d.data));
  }, []);

  const greenMoves = movements.filter(m => m.movement_type === 'DOWN');
  const redMoves = movements.filter(m => m.movement_type === 'UP');

  return (
    <Card>
      <h2>📊 Line Movements</h2>
      
      {/* GREEN Section */}
      <Section title="✅ GREEN (Price Down)" color="green">
        <Table>
          <thead>
            <tr>
              <th>Bookmaker</th>
              <th>Old</th>
              <th>New</th>
              <th>Change</th>
              <th>Significance</th>
            </tr>
          </thead>
          <tbody>
            {greenMoves.map(m => (
              <tr key={m.id}>
                <td>{m.bookmaker}</td>
                <td>{m.old_odds?.toFixed(2)}</td>
                <td>{m.new_odds?.toFixed(2)}</td>
                <td style={{color: 'green'}}>
                  {m.price_change_percent > 0 ? '+' : ''}{m.price_change_percent?.toFixed(2)}%
                </td>
                <td>
                  <Badge color={getSeverityColor(m.significance_level)}>
                    {m.significance_level}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Section>

      {/* RED Section */}
      <Section title="❌ RED (Price Up)" color="red">
        <Table>
          <thead>
            <tr>
              <th>Bookmaker</th>
              <th>Old</th>
              <th>New</th>
              <th>Change</th>
              <th>Significance</th>
            </tr>
          </thead>
          <tbody>
            {redMoves.map(m => (
              <tr key={m.id}>
                <td>{m.bookmaker}</td>
                <td>{m.old_odds?.toFixed(2)}</td>
                <td>{m.new_odds?.toFixed(2)}</td>
                <td style={{color: 'red'}}>
                  {m.price_change_percent > 0 ? '+' : ''}{m.price_change_percent?.toFixed(2)}%
                </td>
                <td>
                  <Badge color={getSeverityColor(m.significance_level)}>
                    {m.significance_level}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Section>

      <Refresh onRefresh={() => window.location.reload()} />
    </Card>
  );
}

function getSeverityColor(level) {
  if (level === 'MAJOR') return 'critical-red';
  if (level === 'MODERATE') return 'warning-orange';
  return 'info-gray';
}

export default LineMovementsCard;
```

---

### Card 2: Prop Alerts (High-Value Props)

#### Display Format
```
┌────────────────────────────────────────────────────┐
│ ⭐ PROP ALERTS - Hot Player Props                  │
├────────────────────────────────────────────────────┤
│                                                     │
│ 🔴 HIGH EV (>5%)                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │ LeBron James - Points OVER 28.5               │ │
│  │ Over: 1.91 | Under: 1.91                      │ │
│  │ EV: +5.2% | Best Book: Sportsbet             │ │
│  │                                              │ │
│  │ Jayson Tatum - Assists UNDER 6.5              │ │
│  │ Over: 1.85 | Under: 2.05                      │ │
│  │ EV: +4.1% | Best Book: Pointsbet             │ │
│  └──────────────────────────────────────────────┘ │
│                                                     │
│ 🟡 MEDIUM EV (3-5%)                               │
│  ┌──────────────────────────────────────────────┐ │
│  │ Kemba Walker - Points OVER 18.5                │ │
│  │ Over: 1.88 | Under: 1.92                      │ │
│  │ EV: +3.5% | Best Book: Tab                   │ │
│  └──────────────────────────────────────────────┘ │
│                                                     │
│ ⚪ LOW EV (1-3%)                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │ Marcus Smart - Steals OVER 1.5                 │ │
│  │ Over: 1.90 | Under: 1.90                      │ │
│  │ EV: +1.8% | Best Book: Neds                  │ │
│  └──────────────────────────────────────────────┘ │
│                                                     │
└────────────────────────────────────────────────────┘
```

#### React Component
```jsx
import React from 'react';

function PropAlertsCard() {
  const [alerts, setAlerts] = React.useState([]);
  const [filter, setFilter] = React.useState('HIGH');

  React.useEffect(() => {
    fetch(`/api/prop-alerts?severity=${filter}&active_only=true`)
      .then(r => r.json())
      .then(d => setAlerts(d.data));
  }, [filter]);

  const groupedBySeverity = {
    HIGH: alerts.filter(a => a.severity === 'HIGH'),
    MEDIUM: alerts.filter(a => a.severity === 'MEDIUM'),
    LOW: alerts.filter(a => a.severity === 'LOW'),
  };

  return (
    <Card>
      <h2>⭐ Prop Alerts</h2>
      
      <FilterButtons>
        {['HIGH', 'MEDIUM', 'LOW'].map(sev => (
          <Button
            key={sev}
            active={filter === sev}
            onClick={() => setFilter(sev)}
          >
            {getSeverityEmoji(sev)} {sev}
          </Button>
        ))}
      </FilterButtons>

      {['HIGH', 'MEDIUM', 'LOW'].map(severity => (
        <Section key={severity} title={getSeverityTitle(severity)}>
          {groupedBySeverity[severity].length === 0 ? (
            <p style={{color: 'gray'}}>No {severity} props found</p>
          ) : (
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
              {groupedBySeverity[severity].map(alert => (
                <PropCard key={alert.id} alert={alert} />
              ))}
            </div>
          )}
        </Section>
      ))}

      <Refresh onRefresh={() => window.location.reload()} />
    </Card>
  );
}

function PropCard({ alert }) {
  const isBetterSide = alert.best_side === 'OVER' 
    ? alert.over_odds > alert.under_odds 
    : alert.under_odds > alert.over_odds;

  return (
    <div style={{
      border: '1px solid #ddd',
      padding: '12px',
      borderRadius: '8px',
      background: 'white'
    }}>
      <h4>{alert.player_name}</h4>
      <p style={{margin: '4px 0', fontSize: '14px'}}>
        {alert.prop_market} {alert.best_side} {alert.prop_line}
      </p>
      
      <div style={{display: 'flex', justifyContent: 'space-between', marginTop: '8px'}}>
        <div>
          <small>OVER</small>
          <div style={{
            fontSize: '16px',
            fontWeight: 'bold',
            color: alert.best_side === 'OVER' ? 'green' : '#999'
          }}>
            {alert.over_odds?.toFixed(2)}
          </div>
        </div>
        <div style={{textAlign: 'center'}}>
          <small>EV</small>
          <div style={{fontSize: '18px', fontWeight: 'bold', color: 'blue'}}>
            +{alert.ev_percent?.toFixed(1)}%
          </div>
        </div>
        <div style={{textAlign: 'right'}}>
          <small>UNDER</small>
          <div style={{
            fontSize: '16px',
            fontWeight: 'bold',
            color: alert.best_side === 'UNDER' ? 'green' : '#999'
          }}>
            {alert.under_odds?.toFixed(2)}
          </div>
        </div>
      </div>

      <small style={{display: 'block', marginTop: '8px', color: '#666'}}>
        {alert.best_book}
      </small>
    </div>
  );
}

function getSeverityEmoji(severity) {
  if (severity === 'HIGH') return '🔴';
  if (severity === 'MEDIUM') return '🟡';
  return '⚪';
}

function getSeverityTitle(severity) {
  if (severity === 'HIGH') return '🔴 HIGH EV (>5%)';
  if (severity === 'MEDIUM') return '🟡 MEDIUM EV (3-5%)';
  return '⚪ LOW EV (1-3%)';
}

export default PropAlertsCard;
```

---

## API Endpoints

### GET /api/line-movements
**Get price changes between extractions**

```javascript
// Example request
fetch('/api/line-movements?sport=basketball_nba&movement_type=DOWN&significant_only=true&limit=50')
  .then(r => r.json())
  .then(data => console.log(data));

// Response
{
  "total": 15,
  "data": [
    {
      "sport": "basketball_nba",
      "event_id": "event123",
      "market": "h2h",
      "selection": "Boston Celtics",
      "bookmaker": "Sportsbet",
      "old_odds": 1.95,
      "new_odds": 1.92,
      "price_change": -0.03,
      "price_change_percent": -1.54,
      "movement_type": "DOWN",  // 'DOWN'=Green, 'UP'=Red
      "movement_percent": 1.54,
      "is_significant": false,
      "significance_level": "MINOR",
      "detected_at": "2025-12-11T10:30:00"
    }
  ]
}
```

**Query Parameters:**
- `sport`: Filter by sport (optional)
- `movement_type`: 'UP' or 'DOWN' (optional)
- `significant_only`: true/false (default: false)
- `limit`: 1-1000 (default: 100)

---

### GET /api/prop-alerts
**Get high-value player prop opportunities**

```javascript
// Example request
fetch('/api/prop-alerts?sport=basketball_nba&severity=HIGH&active_only=true&limit=50')
  .then(r => r.json())
  .then(data => console.log(data));

// Response
{
  "total": 8,
  "data": [
    {
      "sport": "basketball_nba",
      "event_id": "event789",
      "player_name": "LeBron James",
      "prop_market": "player_points",
      "prop_line": 28.5,
      "over_odds": 1.91,
      "under_odds": 1.91,
      "best_side": "OVER",  // 'OVER' or 'UNDER'
      "best_book": "Sportsbet",
      "ev_percent": 5.2,
      "alert_type": "HIGH_EV",
      "severity": "HIGH",  // 'HIGH', 'MEDIUM', 'LOW'
      "is_active": true,
      "detected_at": "2025-12-11T10:35:00"
    }
  ]
}
```

**Query Parameters:**
- `sport`: Filter by sport (optional)
- `severity`: 'HIGH', 'MEDIUM', 'LOW' (optional)
- `active_only`: true/false (default: true)
- `limit`: 1-1000 (default: 100)

---

## Color Coding Guide

### Line Movements
| Movement | Color | Meaning |
|----------|-------|---------|
| **DOWN** | 🟢 Green | Price decreased - better odds for bettor |
| **UP** | 🔴 Red | Price increased - worse odds for bettor |
| **SAME** | ⚪ Gray | No change |

### Significance Levels
| Level | Threshold | Color |
|-------|-----------|-------|
| **MAJOR** | >5% change | Critical (bright red) |
| **MODERATE** | 2-5% change | Warning (orange) |
| **MINOR** | <2% change | Info (gray) |

### Prop Alert Severity
| Severity | EV Range | Color | Icon |
|----------|----------|-------|------|
| **HIGH** | ≥5% | Red 🔴 | Highest priority |
| **MEDIUM** | 3-5% | Orange 🟡 | Medium priority |
| **LOW** | 1-3% | Gray ⚪ | Lower priority |

---

## Integration Steps

1. **Add LineMovementsCard to Dashboard:**
   ```jsx
   import LineMovementsCard from './components/LineMovementsCard';
   
   function Dashboard() {
     return (
       <>
         <LineMovementsCard />
         <PropAlertsCard />
       </>
     );
   }
   ```

2. **Refresh Data:**
   - Auto-refresh every 30 seconds
   - Manual refresh button
   - Real-time WebSocket (future enhancement)

3. **Mobile Responsive:**
   - Collapse to accordion on mobile
   - Sort by significance
   - Filter controls

---

## Files Required

### Backend
- ✅ `backend_api.py` - API endpoints (already updated)
- ✅ `create_tables_enhanced.sql` - Database schema
- ✅ `pipeline_v2/line_movement_detector.py` - Detection logic

### Frontend (To Create)
- `components/LineMovementsCard.js` - Line movements display
- `components/PropAlertsCard.js` - Prop alerts display
- `api/movementClient.js` - API calls wrapper
- `styles/LineMovements.css` - Styling

---

Ready to build the UI! 🚀
