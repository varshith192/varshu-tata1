"""
Dynamic Asset Health & Maintenance Calculation Engine

Adaptive calculation that adjusts weights, thresholds, and maintenance timing based on:
- Equipment type and operational mode
- Real-time sensor trends and degradation velocity
- Production impact and criticality
- Historical maintenance patterns
- Seasonal variations and operating conditions
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger("Stelos.DynamicHealth")

# ─────────────────────────────────────────────────────────────────
# EQUIPMENT-SPECIFIC OPERATIONAL PROFILES
# ─────────────────────────────────────────────────────────────────

EQUIPMENT_PROFILES = {
    "pump": {
        "base_weights": {"temperature": 0.40, "vibration": 0.35, "pressure": 0.15, "oil_temp": 0.10},
        "seasonal_adjustments": {
            "summer": {"temperature": 0.45, "vibration": 0.30},  # temp more critical in summer
            "winter": {"temperature": 0.35, "vibration": 0.40},  # vibration more in cold
        },
        "degradation_curves": {
            "slow": 0.2,    # 2% HI loss per day (new equipment)
            "normal": 0.5,  # 5% HI loss per day
            "fast": 1.2,    # 12% HI loss per day (critical state)
            "critical": 2.5, # 25% HI loss per day (emergency)
        },
        "threshold_ranges": {
            "temperature": {"low": 55, "nominal": 65, "warn": 78, "critical": 85, "trip": 95},
            "vibration": {"low": 0.15, "nominal": 0.30, "warn": 0.50, "critical": 0.70, "trip": 1.0},
            "pressure": {"low": 90, "nominal": 100, "warn_low": 85, "warn_high": 115, "critical_high": 120},
        },
        "maintenance_windows": {
            "routine": 30,      # days between routine maintenance
            "planned": 60,      # days for planned major maintenance
            "emergency": 0.5,   # hours before critical failure expected
        }
    },
    "fan": {
        "base_weights": {"temperature": 0.30, "vibration": 0.45, "pressure": 0.15, "oil_temp": 0.10},
        "seasonal_adjustments": {
            "summer": {"temperature": 0.35, "vibration": 0.40},
            "winter": {"temperature": 0.25, "vibration": 0.50},
        },
        "degradation_curves": {
            "slow": 0.15,
            "normal": 0.4,
            "fast": 1.0,
            "critical": 2.0,
        },
        "threshold_ranges": {
            "temperature": {"low": 50, "nominal": 60, "warn": 75, "critical": 83, "trip": 92},
            "vibration": {"low": 0.12, "nominal": 0.25, "warn": 0.45, "critical": 0.65, "trip": 0.95},
        },
        "maintenance_windows": {
            "routine": 45,
            "planned": 90,
            "emergency": 2.0,
        }
    },
    "conveyor": {
        "base_weights": {"temperature": 0.25, "vibration": 0.50, "pressure": 0.15, "oil_temp": 0.10},
        "seasonal_adjustments": {
            "summer": {"vibration": 0.45},
            "winter": {"vibration": 0.55},
        },
        "degradation_curves": {
            "slow": 0.1,
            "normal": 0.3,
            "fast": 0.8,
            "critical": 1.8,
        },
        "threshold_ranges": {
            "temperature": {"low": 45, "nominal": 55, "warn": 70, "critical": 80, "trip": 90},
            "vibration": {"low": 0.10, "nominal": 0.28, "warn": 0.48, "critical": 0.68, "trip": 0.90},
        },
        "maintenance_windows": {
            "routine": 60,
            "planned": 120,
            "emergency": 4.0,
        }
    },
    "furnace": {
        "base_weights": {"temperature": 0.50, "vibration": 0.25, "pressure": 0.15, "oil_temp": 0.10},
        "seasonal_adjustments": {
            "summer": {"temperature": 0.55, "vibration": 0.20},
            "winter": {"temperature": 0.45, "vibration": 0.30},
        },
        "degradation_curves": {
            "slow": 0.3,
            "normal": 0.8,
            "fast": 1.5,
            "critical": 3.0,
        },
        "threshold_ranges": {
            "temperature": {"low": 80, "nominal": 150, "warn": 200, "critical": 230, "trip": 260},
            "vibration": {"low": 0.10, "nominal": 0.20, "warn": 0.35, "critical": 0.55, "trip": 0.80},
        },
        "maintenance_windows": {
            "routine": 14,
            "planned": 45,
            "emergency": 1.0,
        }
    },
    "mill": {
        "base_weights": {"temperature": 0.35, "vibration": 0.45, "pressure": 0.15, "oil_temp": 0.05},
        "seasonal_adjustments": {
            "summer": {"vibration": 0.40, "temperature": 0.40},
            "winter": {"vibration": 0.50, "temperature": 0.30},
        },
        "degradation_curves": {
            "slow": 0.2,
            "normal": 0.6,
            "fast": 1.3,
            "critical": 2.5,
        },
        "threshold_ranges": {
            "temperature": {"low": 60, "nominal": 75, "warn": 85, "critical": 95, "trip": 110},
            "vibration": {"low": 0.15, "nominal": 0.35, "warn": 0.55, "critical": 0.75, "trip": 1.0},
        },
        "maintenance_windows": {
            "routine": 21,
            "planned": 60,
            "emergency": 1.5,
        }
    },
}

# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def get_season(timestamp: Optional[datetime] = None) -> str:
    """Determine season: summer (May-Sep), winter (Oct-Apr)."""
    if timestamp is None:
        timestamp = datetime.now()
    month = timestamp.month
    return "summer" if 5 <= month <= 9 else "winter"


def get_adaptive_weights(
    equipment_type: str,
    health_index: float,
    sensor_trend_velocity: Dict[str, float],
    season: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate adaptive weights based on:
    - Equipment type
    - Current health state (lower HI → more critical sensors get higher weight)
    - Sensor degradation velocity
    - Season
    """
    if equipment_type not in EQUIPMENT_PROFILES:
        equipment_type = "pump"
    
    profile = EQUIPMENT_PROFILES[equipment_type]
    weights = profile["base_weights"].copy()
    
    # Apply seasonal adjustment if provided
    if season is None:
        season = get_season()
    
    seasonal_adj = profile["seasonal_adjustments"].get(season, {})
    for sensor, adj_weight in seasonal_adj.items():
        if sensor in weights:
            weights[sensor] = adj_weight
    
    # Health-state adaptive weighting: when HI is low, emphasize the worst sensors
    if health_index < 60:  # Critical state
        # Increase weight on sensors with negative trends
        for sensor, velocity in sensor_trend_velocity.items():
            if sensor in weights and velocity > 0.5:  # Fast deterioration
                weights[sensor] *= 1.3  # Up to 30% more weight
    elif health_index < 75:  # Warning state
        for sensor, velocity in sensor_trend_velocity.items():
            if sensor in weights and velocity > 0.3:
                weights[sensor] *= 1.15  # Up to 15% more weight
    
    # Normalize to sum to 1.0
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}
    
    return weights


def normalize_sensor_reading(
    sensor_name: str,
    reading_value: float,
    equipment_type: str
) -> Tuple[float, str]:
    """
    Normalize sensor reading to 0-100 health scale and classify state.
    Returns (health_factor, state_label)
    
    States: EXCELLENT (90-100), GOOD (75-90), FAIR (60-75), POOR (40-60), CRITICAL (<40)
    """
    if equipment_type not in EQUIPMENT_PROFILES:
        equipment_type = "pump"
    
    profile = EQUIPMENT_PROFILES[equipment_type]
    thresholds = profile["threshold_ranges"].get(sensor_name, {})
    
    if not thresholds:
        return 100.0, "UNKNOWN"
    
    # Get relevant thresholds
    nominal = thresholds.get("nominal", 0)
    trip = thresholds.get("trip", nominal * 1.5)
    low_threshold = thresholds.get("low", nominal * 0.7)
    warn_threshold = thresholds.get("warn", nominal * 1.2)
    critical_threshold = thresholds.get("critical", nominal * 1.3)
    
    # Bidirectional: penalize both high and low deviations
    if sensor_name in ["temperature", "vibration"]:
        # Higher is worse
        if reading_value < nominal:
            # Sub-nominal is okay but not ideal
            health = 100 - ((nominal - reading_value) / (nominal - low_threshold) * 10)
            health = max(90, min(100, health))
        elif reading_value < warn_threshold:
            health = 100 - ((reading_value - nominal) / (warn_threshold - nominal) * 15)
        elif reading_value < critical_threshold:
            health = 75 - ((reading_value - warn_threshold) / (critical_threshold - warn_threshold) * 25)
        elif reading_value < trip:
            health = 40 - ((reading_value - critical_threshold) / (trip - critical_threshold) * 35)
        else:
            health = 0
    elif sensor_name == "pressure":
        # Pressure can be too high or too low
        warn_low = thresholds.get("warn_low", nominal * 0.85)
        warn_high = thresholds.get("warn_high", nominal * 1.15)
        
        if warn_low <= reading_value <= warn_high:
            health = 100 - (abs(reading_value - nominal) / max(abs(warn_high - nominal), 1) * 10)
            health = min(100, max(90, health))
        elif reading_value < warn_low or reading_value > warn_high:
            dev = min(
                abs(reading_value - warn_low),
                abs(reading_value - warn_high)
            )
            health = 75 - (dev / 10 * 25)
        else:
            health = 40
    else:
        # Generic normalization
        if reading_value <= nominal:
            health = 95
        elif reading_value < warn_threshold:
            health = 100 - ((reading_value - nominal) / (warn_threshold - nominal) * 20)
        else:
            health = 50
    
    health = max(0.0, min(100.0, health))
    
    # Classify state
    if health >= 90:
        state = "EXCELLENT"
    elif health >= 75:
        state = "GOOD"
    elif health >= 60:
        state = "FAIR"
    elif health >= 40:
        state = "POOR"
    else:
        state = "CRITICAL"
    
    return round(health, 1), state


def compute_trend_velocity(
    sensor_history: List[Dict[str, Any]],
    sensor_name: str,
    hours_window: int = 168
) -> float:
    """
    Calculate degradation velocity: % change in sensor per day.
    Positive = deteriorating, Negative = improving
    
    Returns: degradation rate as float (e.g., 0.5 = 0.5% per day deterioration)
    """
    if not sensor_history or len(sensor_history) < 2:
        return 0.0
    
    # Use most recent readings up to window size
    recent = sensor_history[-min(hours_window, len(sensor_history)):]
    
    values = []
    for reading in recent:
        if sensor_name in reading:
            try:
                values.append(float(reading[sensor_name]))
            except (ValueError, TypeError):
                continue
    
    if len(values) < 2:
        return 0.0
    
    # Linear regression slope
    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    
    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0
    
    slope_per_hour = numerator / denominator
    slope_per_day = slope_per_hour * 24
    
    # Normalize to percentage change per day
    baseline = values[0]
    if baseline == 0:
        return 0.0
    
    pct_change_per_day = (slope_per_day / baseline) * 100
    return round(pct_change_per_day, 2)


def compute_dynamic_health_index(
    sensor_data: Dict[str, Any],
    equipment_type: str,
    sensor_history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Compute health index with adaptive weights and trend analysis.
    
    Parameters
    ----------
    sensor_data : dict
        Current sensor readings {sensor_name: value}
    equipment_type : str
        Type of equipment (pump, fan, conveyor, furnace, mill)
    sensor_history : list, optional
        List of historical readings for trend analysis
    
    Returns
    -------
    dict with:
        health_index : float (0-100)
        health_status : str (EXCELLENT, GOOD, FAIR, POOR, CRITICAL)
        component_scores : dict (individual sensor health)
        trend_velocities : dict (degradation rate per sensor)
        adaptive_weights : dict (calculated weights used)
        degradation_rate_classification : str (slow/normal/fast/critical)
        recommendations : list (suggested actions)
    """
    
    if equipment_type not in EQUIPMENT_PROFILES:
        equipment_type = "pump"
    
    profile = EQUIPMENT_PROFILES[equipment_type]
    season = get_season()
    
    # Step 1: Normalize each sensor reading
    component_scores = {}
    trend_velocities = {}
    
    for sensor_name in ["temperature", "vibration", "pressure", "oil_temp", "motor_current"]:
        if sensor_name in sensor_data:
            reading = sensor_data[sensor_name]
            health, state = normalize_sensor_reading(sensor_name, reading, equipment_type)
            component_scores[sensor_name] = {
                "value": reading,
                "health": health,
                "state": state
            }
        
        # Calculate trend velocity
        if sensor_history:
            velocity = compute_trend_velocity(sensor_history, sensor_name)
            trend_velocities[sensor_name] = velocity
    
    # Step 2: Calculate current health index (temporary to determine state for weighting)
    temp_weights = profile["base_weights"].copy()
    temp_hi = 0.0
    weight_sum = 0.0
    for sensor_name, score_data in component_scores.items():
        if sensor_name in temp_weights:
            temp_hi += score_data["health"] * temp_weights[sensor_name]
            weight_sum += temp_weights[sensor_name]
    
    if weight_sum > 0:
        temp_hi /= weight_sum
    
    # Step 3: Get adaptive weights based on current state
    adaptive_weights = get_adaptive_weights(
        equipment_type,
        temp_hi,
        trend_velocities,
        season
    )
    
    # Step 4: Calculate final health index with adaptive weights
    health_index = 0.0
    for sensor_name, score_data in component_scores.items():
        if sensor_name in adaptive_weights:
            health_index += score_data["health"] * adaptive_weights[sensor_name]
    
    health_index = round(min(100.0, max(0.0, health_index)), 1)
    
    # Step 5: Classify health status
    if health_index >= 90:
        health_status = "EXCELLENT"
    elif health_index >= 75:
        health_status = "GOOD"
    elif health_index >= 60:
        health_status = "FAIR"
    elif health_index >= 40:
        health_status = "POOR"
    else:
        health_status = "CRITICAL"
    
    # Step 6: Classify degradation rate
    avg_velocity = sum(abs(v) for v in trend_velocities.values()) / max(len(trend_velocities), 1)
    if avg_velocity < 0.2:
        degradation_rate = "slow"
    elif avg_velocity < 0.5:
        degradation_rate = "normal"
    elif avg_velocity < 1.2:
        degradation_rate = "fast"
    else:
        degradation_rate = "critical"
    
    # Step 7: Generate recommendations
    recommendations = _generate_recommendations(
        health_index,
        health_status,
        component_scores,
        trend_velocities,
        equipment_type,
        degradation_rate
    )
    
    return {
        "health_index": health_index,
        "health_status": health_status,
        "component_scores": component_scores,
        "trend_velocities": trend_velocities,
        "adaptive_weights": adaptive_weights,
        "degradation_rate_classification": degradation_rate,
        "season": season,
        "equipment_type": equipment_type,
        "recommendations": recommendations,
    }


def _generate_recommendations(
    health_index: float,
    health_status: str,
    component_scores: Dict,
    trend_velocities: Dict,
    equipment_type: str,
    degradation_rate: str
) -> List[str]:
    """Generate actionable maintenance recommendations."""
    recommendations = []
    
    # Critical component-specific recommendations
    for sensor_name, score_data in component_scores.items():
        if score_data["state"] == "CRITICAL":
            recommendations.append(
                f"URGENT: {sensor_name.replace('_', ' ').title()} critical ({score_data['value']}). "
                f"Schedule emergency maintenance immediately."
            )
        elif score_data["state"] == "POOR":
            velocity = trend_velocities.get(sensor_name, 0)
            if velocity > 1.0:
                recommendations.append(
                    f"⚠ {sensor_name.replace('_', ' ').title()} deteriorating rapidly "
                    f"({velocity:+.2f}%/day). Plan maintenance within 7 days."
                )
    
    # Overall health recommendations
    if health_status == "CRITICAL":
        recommendations.append(
            "Equipment in critical state. Reduce production load and prioritize repair."
        )
    elif health_status == "POOR":
        recommendations.append(
            f"Health declining ({degradation_rate} degradation rate). "
            "Plan maintenance within 2 weeks."
        )
    elif health_status == "FAIR":
        if degradation_rate in ["fast", "critical"]:
            recommendations.append(
                "Health declining. Schedule maintenance before next planned downtime."
            )
    
    # Trend-based recommendations
    worst_trends = sorted(
        [(k, v) for k, v in trend_velocities.items() if v > 0.3],
        key=lambda x: x[1],
        reverse=True
    )
    
    if worst_trends:
        sensor, velocity = worst_trends[0]
        recommendations.append(
            f"Focus inspection on {sensor.replace('_', ' ')} "
            f"(trending {velocity:+.2f}%/day). May indicate bearing wear or imbalance."
        )
    
    if not recommendations:
        recommendations.append("Equipment operating nominally. Continue routine monitoring.")
    
    return recommendations


def compute_maintenance_schedule(
    equipment_id: str,
    equipment_type: str,
    health_index: float,
    health_status: str,
    last_maintenance: Optional[datetime] = None,
    production_schedule: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Calculate optimal maintenance schedule based on:
    - Health state and degradation rate
    - Equipment criticality
    - Production schedule (find optimal windows)
    - Previous maintenance history
    
    Returns
    -------
    dict with:
        next_maintenance_date : datetime
        maintenance_type : str (routine/planned/emergency)
        urgency_level : str (low/medium/high/critical)
        estimated_downtime_hours : float
        production_loss_estimate : float (₹)
        confidence_level : float (0-1)
    """
    
    if equipment_type not in EQUIPMENT_PROFILES:
        equipment_type = "pump"
    
    profile = EQUIPMENT_PROFILES[equipment_type]
    now = datetime.now()
    
    # Determine maintenance urgency
    if health_index < 40:
        urgency = "critical"
        days_buffer = 0.5
        maintenance_type = "emergency"
    elif health_index < 60:
        urgency = "high"
        days_buffer = 2
        maintenance_type = "planned"
    elif health_index < 75:
        urgency = "medium"
        days_buffer = 7
        maintenance_type = "planned"
    else:
        urgency = "low"
        days_buffer = profile["maintenance_windows"]["routine"] // 2
        maintenance_type = "routine"
    
    # Calculate next maintenance date
    if last_maintenance:
        days_since = (now - last_maintenance).days
        interval = profile["maintenance_windows"][maintenance_type]
        days_until = max(days_buffer, interval - days_since)
    else:
        days_until = days_buffer
    
    next_maintenance = now + timedelta(days=days_until)
    
    # Try to schedule during production downtime if available
    if production_schedule:
        next_maintenance = _optimize_maintenance_window(
            next_maintenance,
            production_schedule
        )
    
    # Estimate downtime (varies by maintenance type)
    downtime_map = {
        "routine": 2,      # 2 hours for oil change, inspection
        "planned": 8,      # 8 hours for bearing replacement, etc.
        "emergency": 1,    # Already half-failed
    }
    estimated_downtime = downtime_map.get(maintenance_type, 4)
    
    # Confidence level decreases if health rapidly deteriorating
    confidence = min(0.99, max(0.5, (100 - health_index) / 100))
    
    return {
        "equipment_id": equipment_id,
        "next_maintenance_date": next_maintenance.isoformat(),
        "maintenance_type": maintenance_type,
        "urgency_level": urgency,
        "days_until_recommended": round(days_until, 1),
        "estimated_downtime_hours": estimated_downtime,
        "confidence_level": round(confidence, 2),
    }


def _optimize_maintenance_window(
    preferred_date: datetime,
    production_schedule: List[Dict]
) -> datetime:
    """Find closest available maintenance window in production schedule."""
    # This is a placeholder - in production, integrate with real production schedule
    # For now, just return preferred date
    return preferred_date


def compute_alert_level(
    health_index: float,
    component_scores: Dict[str, Any],
    trend_velocities: Dict[str, float],
    equipment_type: str
) -> str:
    """
    Dynamically compute alert level based on health state and trends.
    
    Returns: "NORMAL", "WARNING", "CRITICAL", or "EMERGENCY"
    """
    
    # Check for any critical component
    for sensor_data in component_scores.values():
        if sensor_data["state"] == "CRITICAL":
            return "EMERGENCY"
    
    # Check for poor components with bad trends
    poor_fast_trend = any(
        score_data["state"] == "POOR" and 
        trend_velocities.get(sensor, 0) > 1.0
        for sensor, score_data in component_scores.items()
    )
    
    if poor_fast_trend:
        return "CRITICAL"
    
    # Health-based thresholds
    if health_index < 50:
        return "CRITICAL"
    elif health_index < 65:
        return "WARNING"
    else:
        return "NORMAL"
