"""
LINE MOVEMENT DETECTOR
Compares current odds with previous extraction to detect price changes.
Generates GREEN (price down) and RED (price up) alerts.
Also detects prop alert opportunities.
"""
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PriceMovement:
    """Represents a detected price movement"""
    sport: str
    event_id: str
    market: str
    point: Optional[float]
    selection: str
    player_name: Optional[str]
    bookmaker: str
    
    old_odds: Optional[float]
    new_odds: float
    old_extracted_at: Optional[datetime]
    new_extracted_at: datetime
    
    # Calculated
    price_change: float  # new - old
    price_change_percent: float  # (new - old) / old * 100
    movement_type: str  # 'DOWN' (Green), 'UP' (Red), 'SAME'
    movement_percent: float  # absolute percent
    is_significant: bool
    significance_level: str  # 'MINOR', 'MODERATE', 'MAJOR'
    
    def to_dict(self):
        return {
            'sport': self.sport,
            'event_id': self.event_id,
            'market': self.market,
            'point': self.point,
            'selection': self.selection,
            'player_name': self.player_name,
            'bookmaker': self.bookmaker,
            'old_odds': self.old_odds,
            'new_odds': self.new_odds,
            'price_change': self.price_change,
            'price_change_percent': self.price_change_percent,
            'movement_type': self.movement_type,
            'movement_percent': self.movement_percent,
            'is_significant': self.is_significant,
            'significance_level': self.significance_level,
        }


@dataclass
class PropAlert:
    """Represents a detected prop opportunity"""
    sport: str
    event_id: str
    player_name: str
    prop_market: str
    prop_line: Optional[float]
    over_odds: Optional[float]
    under_odds: Optional[float]
    best_side: str  # 'OVER' or 'UNDER'
    best_book: str
    ev_percent: float
    alert_type: str  # 'HIGH_EV', 'LINE_MOVE', 'SHARP_SIGNAL', 'NEW_PROP'
    severity: str  # 'LOW', 'MEDIUM', 'HIGH'
    
    def to_dict(self):
        return {
            'sport': self.sport,
            'event_id': self.event_id,
            'player_name': self.player_name,
            'prop_market': self.prop_market,
            'prop_line': self.prop_line,
            'over_odds': self.over_odds,
            'under_odds': self.under_odds,
            'best_side': self.best_side,
            'best_book': self.best_book,
            'ev_percent': ev_percent,
            'alert_type': self.alert_type,
            'severity': self.severity,
        }


class LineMovementDetector:
    """Detects price changes between consecutive odds extractions"""
    
    # Thresholds for significance
    SIGNIFICANT_THRESHOLD = 0.03  # 3% absolute change triggers "significant"
    MAJOR_THRESHOLD = 0.05  # 5% triggers "MAJOR"
    MODERATE_THRESHOLD = 0.02  # 2% triggers "MODERATE"
    
    def __init__(self, previous_odds_csv: Optional[Path] = None, current_odds_csv: Optional[Path] = None):
        """
        Initialize detector with previous and current odds CSVs.
        
        Args:
            previous_odds_csv: Path to previous extraction CSV
            current_odds_csv: Path to current extraction CSV
        """
        self.previous_odds = self._load_csv(previous_odds_csv) if previous_odds_csv else {}
        self.current_odds = self._load_csv(current_odds_csv) if current_odds_csv else {}
        self.movements: List[PriceMovement] = []
    
    @staticmethod
    def _load_csv(csv_path: Path) -> Dict:
        """Load CSV into a keyed dictionary for fast lookup"""
        data = {}
        if not csv_path or not csv_path.exists():
            return data
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Create key: (event_id, market, point, selection, bookmaker)
                    key = (
                        row.get('event_id', ''),
                        row.get('market', ''),
                        row.get('point', ''),
                        row.get('selection', ''),
                        row.get('bookmaker', '')
                    )
                    data[key] = row
        except Exception as e:
            print(f"[!] Error loading CSV {csv_path}: {e}")
        
        return data
    
    def detect_movements(self) -> List[PriceMovement]:
        """
        Compare current odds against previous odds.
        Returns list of detected price movements.
        """
        movements = []
        
        # For each current odds entry, find if there was a previous entry
        for current_key, current_row in self.current_odds.items():
            if current_key not in self.previous_odds:
                # This is a new line (no previous extraction)
                continue
            
            previous_row = self.previous_odds[current_key]
            
            try:
                old_odds = float(previous_row.get('odds', 0)) or None
                new_odds = float(current_row.get('odds', 0))
                
                if old_odds is None or old_odds <= 1 or new_odds <= 1:
                    continue
                
                # Calculate movement
                movement = self._calculate_movement(
                    previous_row,
                    current_row,
                    old_odds,
                    new_odds
                )
                
                if movement:
                    movements.append(movement)
            
            except Exception as e:
                print(f"[!] Error calculating movement for {current_key}: {e}")
                continue
        
        self.movements = movements
        return movements
    
    @staticmethod
    def _calculate_movement(
        prev_row: Dict,
        curr_row: Dict,
        old_odds: float,
        new_odds: float
    ) -> Optional[PriceMovement]:
        """Calculate movement details for a single odds pair"""
        
        # Calculate deltas
        price_change = new_odds - old_odds
        price_change_percent = (price_change / old_odds) * 100 if old_odds > 0 else 0
        movement_percent = abs(price_change_percent)
        
        # Determine movement type
        if price_change < -0.01:  # Odds decreased (better for bettor)
            movement_type = 'DOWN'  # Green
        elif price_change > 0.01:  # Odds increased (worse for bettor)
            movement_type = 'UP'  # Red
        else:
            movement_type = 'SAME'
        
        # Determine significance
        is_significant = movement_percent >= LineMovementDetector.SIGNIFICANT_THRESHOLD
        
        if movement_percent >= LineMovementDetector.MAJOR_THRESHOLD:
            significance_level = 'MAJOR'
        elif movement_percent >= LineMovementDetector.MODERATE_THRESHOLD:
            significance_level = 'MODERATE'
        else:
            significance_level = 'MINOR'
        
        return PriceMovement(
            sport=curr_row.get('sport', ''),
            event_id=curr_row.get('event_id', ''),
            market=curr_row.get('market', ''),
            point=float(curr_row.get('point') or 0) or None,
            selection=curr_row.get('selection', ''),
            player_name=curr_row.get('player', None),  # For props
            bookmaker=curr_row.get('bookmaker', ''),
            old_odds=old_odds,
            new_odds=new_odds,
            old_extracted_at=datetime.fromisoformat(prev_row.get('timestamp', '')) if prev_row.get('timestamp') else None,
            new_extracted_at=datetime.fromisoformat(curr_row.get('timestamp', '')) if curr_row.get('timestamp') else None,
            price_change=price_change,
            price_change_percent=price_change_percent,
            movement_type=movement_type,
            movement_percent=movement_percent,
            is_significant=is_significant,
            significance_level=significance_level,
        )
    
    def filter_by_type(self, movement_type: str) -> List[PriceMovement]:
        """Filter movements by type (DOWN = Green, UP = Red, SAME)"""
        return [m for m in self.movements if m.movement_type == movement_type]
    
    def filter_significant(self) -> List[PriceMovement]:
        """Get only significant movements"""
        return [m for m in self.movements if m.is_significant]
    
    def get_green_movements(self) -> List[PriceMovement]:
        """Get DOWN movements (price decreased - GREEN)"""
        return self.filter_by_type('DOWN')
    
    def get_red_movements(self) -> List[PriceMovement]:
        """Get UP movements (price increased - RED)"""
        return self.filter_by_type('UP')
    
    def write_movements_csv(self, output_path: Path):
        """Write detected movements to CSV"""
        if not self.movements:
            print(f"[!] No movements to write")
            return
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'detected_at', 'sport', 'event_id', 'market', 'point', 
                    'selection', 'player_name', 'bookmaker',
                    'old_odds', 'new_odds', 'price_change', 'price_change_percent',
                    'movement_type', 'movement_percent', 'is_significant', 'significance_level'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for movement in self.movements:
                    row = movement.to_dict()
                    row['detected_at'] = datetime.now().isoformat()
                    writer.writerow(row)
            
            print(f"[OK] Wrote {len(self.movements)} line movements to {output_path}")
        
        except Exception as e:
            print(f"[!] Error writing movements CSV: {e}")


class PropAlertDetector:
    """Detects high-value player prop opportunities"""
    
    # EV thresholds for alerting
    HIGH_EV_THRESHOLD = 0.05  # 5% EV triggers alert
    MEDIUM_EV_THRESHOLD = 0.03  # 3% medium
    LOW_EV_THRESHOLD = 0.01  # 1% low
    
    # Line movement thresholds
    SIGNIFICANT_MOVE = 0.03  # 3% movement on prop
    
    def __init__(self):
        self.alerts: List[PropAlert] = []
    
    def detect_from_ev_opportunities(self, ev_opportunities: List[Dict]) -> List[PropAlert]:
        """
        Extract prop alerts from EV opportunities.
        Filters for player_name != None (indicates props).
        """
        prop_alerts = []
        
        for opp in ev_opportunities:
            # Skip non-props
            if not opp.get('player'):
                continue
            
            ev_percent = float(opp.get('ev_percent', 0))
            
            # Determine severity based on EV%
            if ev_percent >= self.HIGH_EV_THRESHOLD:
                severity = 'HIGH'
            elif ev_percent >= self.MEDIUM_EV_THRESHOLD:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
            
            # Determine best side (need to infer from selection)
            selection = opp.get('selection', '')
            best_side = 'OVER' if 'Over' in selection else 'UNDER' if 'Under' in selection else 'UNKNOWN'
            
            alert = PropAlert(
                sport=opp.get('sport', ''),
                event_id=opp.get('event_id', ''),
                player_name=opp.get('player', ''),
                prop_market=opp.get('market', ''),
                prop_line=opp.get('point'),
                over_odds=opp.get('best_odds') if best_side == 'OVER' else None,
                under_odds=opp.get('best_odds') if best_side == 'UNDER' else None,
                best_side=best_side,
                best_book=opp.get('best_book', ''),
                ev_percent=ev_percent,
                alert_type='HIGH_EV',
                severity=severity,
            )
            
            prop_alerts.append(alert)
        
        self.alerts = prop_alerts
        return prop_alerts
    
    def write_alerts_csv(self, output_path: Path):
        """Write prop alerts to CSV"""
        if not self.alerts:
            print(f"[!] No prop alerts to write")
            return
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'detected_at', 'sport', 'event_id', 'player_name', 'prop_market',
                    'prop_line', 'over_odds', 'under_odds', 'best_side', 'best_book',
                    'ev_percent', 'alert_type', 'severity'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for alert in self.alerts:
                    row = alert.to_dict()
                    row['detected_at'] = datetime.now().isoformat()
                    writer.writerow(row)
            
            print(f"[OK] Wrote {len(self.alerts)} prop alerts to {output_path}")
        
        except Exception as e:
            print(f"[!] Error writing prop alerts CSV: {e}")
