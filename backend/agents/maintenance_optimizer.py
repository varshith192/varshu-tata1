"""
Advanced Maintenance Scheduling & Optimization

Calculates optimal maintenance timing considering:
- Production schedules and downtime windows
- Cost-benefit analysis (repair vs. failure cost)
- Spare parts availability
- Maintenance team capacity
- Equipment interdependencies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import math
import logging

logger = logging.getLogger("Stelos.MaintenanceOptimization")

# ─────────────────────────────────────────────────────────────────
# MAINTENANCE COST MODELS
# ─────────────────────────────────────────────────────────────────

EQUIPMENT_COSTS = {
    "pump": {
        "production_loss_per_hour": 3700000,    # ₹37L/hr (blast furnace cooling)
        "planned_maintenance_cost": 400000,     # ₹4L (oil change, filter, inspection)
        "major_maintenance_cost": 1200000,      # ₹12L (bearing replacement)
        "emergency_repair_cost": 2200000,       # ₹22L (catastrophic failure + rush)
        "spare_lead_time_days": 7,
    },
    "fan": {
        "production_loss_per_hour": 400000,
        "planned_maintenance_cost": 80000,
        "major_maintenance_cost": 300000,
        "emergency_repair_cost": 300000,
        "spare_lead_time_days": 5,
    },
    "conveyor": {
        "production_loss_per_hour": 800000,
        "planned_maintenance_cost": 150000,
        "major_maintenance_cost": 600000,
        "emergency_repair_cost": 600000,
        "spare_lead_time_days": 10,
    },
    "furnace": {
        "production_loss_per_hour": 8300000,
        "planned_maintenance_cost": 2500000,
        "major_maintenance_cost": 8000000,
        "emergency_repair_cost": 15000000,
        "spare_lead_time_days": 14,
    },
    "mill": {
        "production_loss_per_hour": 5800000,
        "planned_maintenance_cost": 800000,
        "major_maintenance_cost": 3000000,
        "emergency_repair_cost": 4500000,
        "spare_lead_time_days": 7,
    },
}

# ─────────────────────────────────────────────────────────────────
# MAINTENANCE OPTIMIZATION
# ─────────────────────────────────────────────────────────────────

def calculate_total_maintenance_cost(
    equipment_type: str,
    maintenance_type: str,
    downtime_hours: float,
    is_emergency: bool = False
) -> Dict[str, float]:
    """
    Calculate total cost of maintenance including:
    - Direct maintenance cost
    - Production loss during downtime
    - Emergency premium if needed
    
    Returns
    -------
    dict with:
        direct_cost : float
        production_loss : float
        emergency_premium : float
        total_cost : float
    """
    
    if equipment_type not in EQUIPMENT_COSTS:
        equipment_type = "pump"
    
    costs = EQUIPMENT_COSTS[equipment_type]
    
    # Direct maintenance cost
    if maintenance_type == "routine":
        direct = costs["planned_maintenance_cost"]
    elif maintenance_type == "planned":
        direct = costs["major_maintenance_cost"]
    else:  # emergency
        direct = costs["emergency_repair_cost"]
    
    # Production loss during downtime
    production_loss = costs["production_loss_per_hour"] * downtime_hours
    
    # Emergency premium (labor, expedited parts, etc.)
    emergency_premium = 0
    if is_emergency:
        emergency_premium = direct * 0.4  # 40% surcharge for emergency response
    
    total = direct + production_loss + emergency_premium
    
    return {
        "direct_cost": round(direct, 0),
        "production_loss": round(production_loss, 0),
        "emergency_premium": round(emergency_premium, 0),
        "total_cost": round(total, 0),
    }


def calculate_failure_cost(
    equipment_type: str,
    hours_until_failure: float,
    maintenance_delay_hours: float = 0
) -> Dict[str, Any]:
    """
    Calculate cost if equipment fails without maintenance.
    
    Includes:
    - Production loss while failed + repair time
    - Secondary failures (cascading damage)
    - Quality degradation of products
    - Emergency repair premium
    
    Returns
    -------
    dict with cost breakdown and probability-weighted expectation
    """
    
    if equipment_type not in EQUIPMENT_COSTS:
        equipment_type = "pump"
    
    costs = EQUIPMENT_COSTS[equipment_type]
    
    # Unplanned downtime is typically 3-5x worse
    if equipment_type == "furnace":
        total_downtime = 24  # Furnace failure typically requires full shift + setup
    elif equipment_type == "mill":
        total_downtime = 16  # Major equipment
    else:
        total_downtime = 6   # Shorter repair for supporting equipment
    
    production_loss = costs["production_loss_per_hour"] * total_downtime
    emergency_repair = costs["emergency_repair_cost"]
    
    # Secondary damage risk (increases with severity)
    severity_factor = 1 + (min(5, 24 - hours_until_failure) / 24)  # Up to 2x for critical
    secondary_damage = emergency_repair * 0.3 * severity_factor
    
    total_failure_cost = production_loss + emergency_repair + secondary_damage
    
    return {
        "total_downtime_hours": total_downtime,
        "production_loss": round(production_loss, 0),
        "emergency_repair_cost": round(emergency_repair, 0),
        "secondary_damage_risk": round(secondary_damage, 0),
        "total_failure_cost": round(total_failure_cost, 0),
    }


def calculate_maintenance_roi(
    equipment_type: str,
    health_index: float,
    hours_until_probable_failure: float,
    maintenance_type: str = "planned",
    downtime_hours: float = 8,
    success_probability: float = 0.95
) -> Dict[str, Any]:
    """
    Calculate ROI of performing maintenance now vs. waiting.
    
    Returns
    -------
    dict with:
        maintenance_cost : float
        expected_failure_cost : float
        roi_value : float (savings if maintenance done now)
        recommendation : str (MAINTAIN_NOW, DELAY, or MONITOR)
    """
    
    # Cost of maintenance now
    maint_cost = calculate_total_maintenance_cost(
        equipment_type,
        maintenance_type,
        downtime_hours,
        is_emergency=False
    )
    
    # Expected cost of failure (weighted by failure probability)
    failure_prob = 1.0 - (health_index / 100.0) ** 2  # Quadratic increase in failure risk
    
    failure_cost = calculate_failure_cost(
        equipment_type,
        hours_until_probable_failure
    )
    
    expected_failure_cost = failure_cost["total_failure_cost"] * failure_prob
    
    # ROI calculation
    roi_value = expected_failure_cost - maint_cost["total_cost"]
    roi_ratio = roi_value / max(maint_cost["total_cost"], 1) if maint_cost["total_cost"] > 0 else 0
    
    # Recommendation logic
    if roi_value > maint_cost["total_cost"] * 0.5:  # If failure cost > 1.5x maintenance cost
        recommendation = "MAINTAIN_NOW"
    elif health_index < 50 or failure_prob > 0.7:
        recommendation = "MAINTAIN_NOW"
    elif health_index < 70 and hours_until_probable_failure < 72:
        recommendation = "MAINTAIN_SOON"
    else:
        recommendation = "MONITOR"
    
    return {
        "maintenance_cost": maint_cost["total_cost"],
        "expected_failure_cost": round(expected_failure_cost, 0),
        "roi_value": round(roi_value, 0),
        "roi_ratio": round(roi_ratio, 2),
        "failure_probability": round(failure_prob, 2),
        "recommendation": recommendation,
    }


class MaintenanceScheduleOptimizer:
    """Optimizes maintenance scheduling across fleet of equipment."""
    
    def __init__(self, fleet_data: List[Dict]):
        """
        Parameters
        ----------
        fleet_data : list of dict
            Fleet status data with keys:
            - equipment_id
            - equipment_type
            - health_index
            - predicted_rul_days
            - location
            - criticality
        """
        self.fleet = fleet_data
        self.now = datetime.now()
    
    def prioritize_maintenance_queue(
        self,
        maintenance_capacity_hours_per_day: float = 8,
        days_planning_horizon: int = 30
    ) -> List[Dict]:
        """
        Prioritize equipment for maintenance based on:
        - Health urgency
        - ROI analysis
        - Production impact
        - Maintenance interdependencies
        - Team capacity constraints
        
        Returns
        -------
        list of dicts with optimized maintenance schedule
        """
        
        # Score each equipment for maintenance urgency
        scored_equipment = []
        for eq in self.fleet:
            score = self._calculate_maintenance_priority_score(eq)
            scored_equipment.append({
                **eq,
                "priority_score": score,
            })
        
        # Sort by priority (highest first)
        scored_equipment.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Allocate maintenance slots respecting capacity
        schedule = []
        cumulative_hours = 0
        
        for eq in scored_equipment:
            if cumulative_hours >= maintenance_capacity_hours_per_day * days_planning_horizon:
                break
            
            # Estimate maintenance duration
            if eq["health_index"] < 40:
                duration = 4  # Emergency quick fix
            elif eq["health_index"] < 60:
                duration = 8  # Major maintenance
            else:
                duration = 2  # Routine
            
            scheduled_date = self.now + timedelta(
                days=math.ceil(cumulative_hours / maintenance_capacity_hours_per_day)
            )
            
            schedule.append({
                "equipment_id": eq["equipment_id"],
                "equipment_type": eq["equipment_type"],
                "location": eq.get("location", "Unknown"),
                "health_index": eq["health_index"],
                "maintenance_duration_hours": duration,
                "scheduled_date": scheduled_date.isoformat(),
                "priority_rank": len(schedule) + 1,
                "priority_score": eq["priority_score"],
            })
            
            cumulative_hours += duration
        
        return schedule
    
    def _calculate_maintenance_priority_score(self, equipment: Dict) -> float:
        """
        Multi-factor scoring for maintenance priority:
        - Health urgency (highest weight)
        - Production criticality
        - RUL prediction
        - Failure risk
        """
        
        hi = equipment.get("health_index", 50)
        criticality = equipment.get("criticality", "Medium")
        rul = equipment.get("predicted_rul_days", 30)
        
        # Health score (0-100, higher = more urgent)
        health_urgency = 100 - hi  # 0 for excellent, 100 for critical
        
        # Criticality multiplier
        criticality_map = {"Critical": 1.5, "High": 1.2, "Medium": 1.0, "Low": 0.7}
        criticality_mult = criticality_map.get(criticality, 1.0)
        
        # RUL urgency (shorter RUL = more urgent)
        rul_urgency = max(0, 30 - rul) / 30 * 30  # 0-30 points
        
        # Combined score
        score = (health_urgency * 0.6 + rul_urgency * 0.3) * criticality_mult
        
        return round(score, 1)
    
    def suggest_batch_maintenance(self) -> List[Dict]:
        """
        Suggest batching maintenance on related equipment to reduce total downtime.
        
        E.g., if Pump-A and Pump-B are in same cooling loop, maintain together.
        
        Returns
        -------
        list of maintenance batches with total expected downtime/cost
        """
        
        # Group by location/subsystem
        by_location = {}
        for eq in self.fleet:
            loc = eq.get("location", "Unknown")
            if loc not in by_location:
                by_location[loc] = []
            by_location[loc].append(eq)
        
        batches = []
        for location, equipment_list in by_location.items():
            # Only batch if multiple pieces need maintenance soon
            urgent = [e for e in equipment_list if e.get("health_index", 100) < 70]
            
            if len(urgent) > 1:
                total_hours = sum(
                    2 if e["health_index"] > 60 else 4 if e["health_index"] > 40 else 6
                    for e in urgent
                )
                total_cost = sum(
                    calculate_total_maintenance_cost(
                        e["equipment_type"],
                        "planned" if e["health_index"] < 70 else "routine",
                        2 if e["health_index"] > 60 else 4,
                    )["total_cost"]
                    for e in urgent
                )
                
                batches.append({
                    "location": location,
                    "equipment_ids": [e["equipment_id"] for e in urgent],
                    "count": len(urgent),
                    "total_downtime_hours": total_hours,
                    "estimated_cost": round(total_cost, 0),
                    "efficiency_gain": f"{round(len(urgent) / 3 * 100)}%",  # vs 3 separate maintenances
                })
        
        return batches


def generate_maintenance_report(
    equipment_data: Dict,
    sensor_history: Optional[List] = None
) -> Dict:
    """
    Generate comprehensive maintenance report for an equipment.
    """
    
    eq_type = equipment_data.get("equipment_type", "pump")
    hi = equipment_data.get("health_index", 50)
    rul = equipment_data.get("predicted_rul_days", 30)
    
    # Calculate costs
    maint_cost = calculate_total_maintenance_cost(eq_type, "planned", 8)
    failure_cost_data = calculate_failure_cost(eq_type, rul * 24)
    roi = calculate_maintenance_roi(eq_type, hi, rul * 24)
    
    return {
        "equipment_id": equipment_data.get("equipment_id", "Unknown"),
        "health_index": hi,
        "predicted_rul_days": rul,
        "maintenance_recommendation": roi["recommendation"],
        "cost_analysis": {
            "planned_maintenance_cost": maint_cost["total_cost"],
            "expected_failure_cost": failure_cost_data["total_failure_cost"],
            "roi_value": roi["roi_value"],
            "break_even_analysis": {
                "cost_to_perform_now": round(maint_cost["total_cost"], 0),
                "cost_of_doing_nothing": round(roi["expected_failure_cost"], 0),
                "savings_by_maintaining_now": round(roi["roi_value"], 0),
            }
        },
        "schedule_recommendation": {
            "maintenance_type": "emergency" if hi < 40 else "planned" if hi < 70 else "routine",
            "urgency": "critical" if hi < 40 else "high" if hi < 60 else "medium" if hi < 75 else "low",
            "suggested_window": f"Next {max(1, int(rul))} days",
        }
    }
