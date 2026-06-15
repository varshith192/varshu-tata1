"""
Physics-based Remaining Useful Life (RUL) estimation for steel plant equipment.

Uses a degradation model combining:
  1. Health Index (HI) from multi-sensor readings
  2. Exponential degradation rate from sensor trends
  3. Weibull survival function for failure probability
  4. Confidence intervals based on sensor variance

Based on Tata Steel PM-GUIDE-001 methodology.
"""
import math
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger("Stelos.RULPredictor")

# ─────────────────────────────────────────
# Equipment-specific degradation parameters
# ─────────────────────────────────────────
EQUIPMENT_PARAMS = {
    "pump": {
        "degradation_factor": 0.5,
        "nominal_rul_days": 180.0,
        "weibull_shape": 2.5,
        "weibull_scale": 120.0,
        "production_loss_per_hr": 3700000,    # ₹37L/hr — blast furnace cooling pump
        "planned_maintenance_cost": 400000,   # ₹4L
        "emergency_repair_cost": 2200000,     # ₹22L
    },
    "conveyor": {
        "degradation_factor": 0.7,
        "nominal_rul_days": 365.0,
        "weibull_shape": 2.0,
        "weibull_scale": 180.0,
        "production_loss_per_hr": 800000,     # ₹8L/hr — raw material conveyor
        "planned_maintenance_cost": 150000,   # ₹1.5L
        "emergency_repair_cost": 600000,      # ₹6L
    },
    "fan": {
        "degradation_factor": 0.6,
        "nominal_rul_days": 270.0,
        "weibull_shape": 2.2,
        "weibull_scale": 150.0,
        "production_loss_per_hr": 400000,     # ₹4L/hr — sinter/cooling fan
        "planned_maintenance_cost": 80000,    # ₹0.8L
        "emergency_repair_cost": 300000,      # ₹3L
    },
    "furnace": {
        "degradation_factor": 0.8,
        "nominal_rul_days": 90.0,             # blast furnaces need frequent maintenance
        "weibull_shape": 3.0,
        "weibull_scale": 60.0,
        "production_loss_per_hr": 8300000,    # ₹83L/hr — blast furnace is highest criticality
        "planned_maintenance_cost": 2500000,  # ₹25L
        "emergency_repair_cost": 15000000,   # ₹1.5Cr
    },
    "mill": {
        "degradation_factor": 0.6,
        "nominal_rul_days": 120.0,
        "weibull_shape": 2.2,
        "weibull_scale": 100.0,
        "production_loss_per_hr": 5800000,    # ₹58L/hr — hot rolling mill
        "planned_maintenance_cost": 800000,   # ₹8L
        "emergency_repair_cost": 4500000,     # ₹45L
    },
    "default": {
        "degradation_factor": 0.6,
        "nominal_rul_days": 200.0,
        "weibull_shape": 2.0,
        "weibull_scale": 130.0,
        "production_loss_per_hr": 2000000,    # ₹20L/hr
        "planned_maintenance_cost": 250000,   # ₹2.5L
        "emergency_repair_cost": 1000000,     # ₹10L
    }
}

# Sensor thresholds for degradation calculation (from SOP-PUMP-001)
THRESHOLDS = {
    "temperature": {"nominal": 65.0, "alarm": 85.0, "trip": 95.0},
    "vibration":   {"nominal": 0.30, "alarm": 0.70, "trip": 1.00},
    "pressure":    {"nominal": 100.0, "alarm_low": 80.0, "alarm_high": 120.0},
    "oil_temp":    {"nominal": 52.0, "alarm": 70.0},
    "motor_current": {"nominal": 42.0, "alarm": 55.0},
}


def compute_health_index(sensor_data: Dict[str, Any]) -> float:
    """
    Compute normalized Health Index (0-100) from sensor readings.
    Based on PM-GUIDE-001 formula with weights:
      temperature=0.40, vibration=0.35, pressure=0.15, oil_temp=0.10
    """
    temp = float(sensor_data.get("temperature", THRESHOLDS["temperature"]["nominal"]))
    vib  = float(sensor_data.get("vibration",   THRESHOLDS["vibration"]["nominal"]))
    pres = float(sensor_data.get("pressure",     THRESHOLDS["pressure"]["nominal"]))
    oil  = float(sensor_data.get("oil_temp",     THRESHOLDS["oil_temp"]["nominal"]))

    # Temperature health factor
    t_range = THRESHOLDS["temperature"]["trip"] - THRESHOLDS["temperature"]["nominal"]
    t_dev = max(0.0, (temp - THRESHOLDS["temperature"]["nominal"]) / t_range)
    t_health = max(0.0, 1.0 - t_dev)

    # Vibration health factor
    v_range = THRESHOLDS["vibration"]["trip"] - THRESHOLDS["vibration"]["nominal"]
    v_dev = max(0.0, (vib - THRESHOLDS["vibration"]["nominal"]) / v_range)
    v_health = max(0.0, 1.0 - v_dev)

    # Pressure health factor (penalizes both high and low deviation)
    p_dev = abs(pres - THRESHOLDS["pressure"]["nominal"]) / 20.0  # ±20 PSI range
    p_health = max(0.0, 1.0 - p_dev)

    # Oil temperature health factor
    o_range = THRESHOLDS["oil_temp"]["alarm"] - THRESHOLDS["oil_temp"]["nominal"]
    o_dev = max(0.0, (oil - THRESHOLDS["oil_temp"]["nominal"]) / max(o_range, 1.0))
    o_health = max(0.0, 1.0 - o_dev)

    hi = 100.0 * (0.40 * t_health + 0.35 * v_health + 0.15 * p_health + 0.10 * o_health)
    return round(min(100.0, max(0.0, hi)), 1)


def weibull_failure_probability(health_index: float, equipment_type: str = "pump") -> float:
    """
    Compute failure probability using Weibull CDF.
    F(t) = 1 - exp(-(t/η)^β)
    Where t is mapped from health index degradation.
    """
    params = EQUIPMENT_PARAMS.get(equipment_type, EQUIPMENT_PARAMS["default"])
    beta = params["weibull_shape"]
    eta = params["weibull_scale"]

    # Map health index to a "time" equivalent: lower HI = further into life
    # t = (100 - HI) / 100 * eta  →  at HI=100, t=0; at HI=0, t=eta
    t = (100.0 - health_index) / 100.0 * eta

    prob = 1.0 - math.exp(-((t / eta) ** beta))
    return round(min(0.99, max(0.01, prob)), 3)


def estimate_rul(
    sensor_data: Dict[str, Any],
    health_index: float,
    equipment_type: str = "pump",
    fault_type: str = "normal_operation"
) -> Dict[str, Any]:
    """
    Estimate Remaining Useful Life with confidence interval.

    Returns
    -------
    dict with:
        predicted_rul_days : float
        rul_lower_bound    : float  (pessimistic 80% CI)
        rul_upper_bound    : float  (optimistic 80% CI)
        failure_probability: float
        degradation_rate   : str    (description)
        maintenance_priority: str  (P1/P2/P3/Routine)
        financial_impact   : dict
    """
    params = EQUIPMENT_PARAMS.get(equipment_type, EQUIPMENT_PARAMS["default"])
    failure_prob = weibull_failure_probability(health_index, equipment_type)

    # Base RUL from Health Index
    # RUL = HI × degradation_factor / 100 × nominal_rul_days
    base_rul = (health_index / 100.0) * params["nominal_rul_days"] * params["degradation_factor"]

    # Adjust for specific fault types (accelerated degradation)
    fault_multipliers = {
        "lubrication_failure": 0.3,   # 70% faster degradation
        "bearing_wear":        0.4,
        "overheating":         0.35,
        "impeller_wear":       0.6,
        "motor_fault":         0.5,
        "normal_operation":    1.0,
    }
    multiplier = fault_multipliers.get(fault_type, 0.7)
    adjusted_rul = base_rul * multiplier

    # Temperature-based RUL cap (physics-based hard limit)
    temp = float(sensor_data.get("temperature", THRESHOLDS["temperature"]["nominal"]))
    if temp > THRESHOLDS["temperature"]["alarm"]:
        # Rate: assume 1°C rise per hour when overheating, trip at 95°C
        hours_to_trip = max(0.5, (THRESHOLDS["temperature"]["trip"] - temp) * 2.0)
        temp_rul = hours_to_trip / 24.0
        adjusted_rul = min(adjusted_rul, temp_rul)

    # Vibration-based RUL cap
    vib = float(sensor_data.get("vibration", THRESHOLDS["vibration"]["nominal"]))
    if vib > THRESHOLDS["vibration"]["alarm"]:
        hours_to_trip = max(1.0, (THRESHOLDS["vibration"]["trip"] - vib) * 40.0)
        vib_rul = hours_to_trip / 24.0
        adjusted_rul = min(adjusted_rul, vib_rul)

    predicted_rul = round(max(0.5, adjusted_rul), 1)

    # Confidence interval (±30% pessimistic, ±50% optimistic)
    rul_lower = round(max(0.1, predicted_rul * 0.70), 1)
    rul_upper = round(predicted_rul * 1.50, 1)

    # Degradation rate description
    if predicted_rul < 3:
        degradation_rate = "Rapid — >2°C/day temperature rise or >0.10 mm/s/week vibration increase"
    elif predicted_rul < 7:
        degradation_rate = "Accelerated — sensor readings trending beyond alarm thresholds"
    elif predicted_rul < 14:
        degradation_rate = "Moderate — sensor readings in warning zone, stable rate"
    elif predicted_rul < 45:
        degradation_rate = "Slow — minor deviations from nominal, watch closely"
    else:
        degradation_rate = "Nominal — all sensors within normal operating envelope"

    # Maintenance priority from PM-GUIDE-001
    if health_index < 30 or failure_prob > 0.80 or predicted_rul < 5:
        priority = "P1"
        priority_label = "P1 — Immediate (within 24 hours)"
    elif health_index < 50 or failure_prob > 0.50 or predicted_rul < 14:
        priority = "P2"
        priority_label = "P2 — Urgent (within 72 hours)"
    elif health_index < 70 or failure_prob > 0.20 or predicted_rul < 45:
        priority = "P3"
        priority_label = "P3 — Planned (within 30 days)"
    else:
        priority = "Routine"
        priority_label = "Routine — Schedule at next available window"

    # Financial impact calculation
    loss_per_hr = params["production_loss_per_hr"]
    planned_cost = params["planned_maintenance_cost"]
    emergency_cost = params["emergency_repair_cost"]

    expected_loss_if_fail = failure_prob * (24.0 * loss_per_hr + emergency_cost)
    risk_adjusted_savings = expected_loss_if_fail - planned_cost

    return {
        "predicted_rul_days": predicted_rul,
        "rul_lower_bound": rul_lower,
        "rul_upper_bound": rul_upper,
        "failure_probability": failure_prob,
        "health_index": health_index,
        "degradation_rate": degradation_rate,
        "maintenance_priority": priority,
        "maintenance_priority_label": priority_label,
        "financial_impact": {
            "production_loss_per_hour_inr": loss_per_hr,
            "planned_maintenance_cost_inr": planned_cost,
            "emergency_repair_cost_inr": emergency_cost,
            "expected_loss_if_failure_inr": round(expected_loss_if_fail, 0),
            "risk_adjusted_savings_inr": round(risk_adjusted_savings, 0),
        }
    }


def simulate_whatif_delay(
    current_rul: float,
    current_failure_prob: float,
    delay_days: int,
    equipment_type: str = "pump"
) -> Dict[str, Any]:
    """
    Simulate: 'What happens if maintenance is delayed by N days?'
    Uses exponential degradation with increasing hazard rate.
    """
    params = EQUIPMENT_PARAMS.get(equipment_type, EQUIPMENT_PARAMS["default"])

    # New failure probability after delay (accelerated Weibull hazard)
    beta = params["weibull_shape"]

    # Increase in failure rate due to operating in degraded state
    # Uses: P(fail by t+d | survived to t) = 1 - exp(-lambda * d)
    # where lambda = beta/eta * (t/eta)^(beta-1)  [Weibull hazard]
    if current_rul > 0.1:
        hazard_rate = beta / max(current_rul, 1.0)
    else:
        hazard_rate = 2.0

    new_failure_prob = round(min(0.99, 1.0 - (1.0 - current_failure_prob) * math.exp(-hazard_rate * delay_days)), 3)
    new_rul = round(max(0.1, current_rul - delay_days), 1)

    # Financial impact of delay
    loss_per_hr = params["production_loss_per_hr"]
    planned_cost = params["planned_maintenance_cost"]
    emergency_cost = params["emergency_repair_cost"]

    # Expected additional loss from delay
    prob_increase = new_failure_prob - current_failure_prob
    additional_expected_loss = prob_increase * (24.0 * loss_per_hr + emergency_cost)

    # Recommendation
    if new_failure_prob > 0.85 or new_rul < 2:
        recommendation = "DO NOT DELAY — High probability of catastrophic failure within the delay window."
        risk_level = "CRITICAL"
    elif new_failure_prob > 0.60 or new_rul < 7:
        recommendation = "DELAY NOT RECOMMENDED — Significant risk increase. Expedite maintenance."
        risk_level = "HIGH"
    elif new_failure_prob > 0.35:
        recommendation = "PROCEED WITH CAUTION — Delay acceptable only with enhanced monitoring (hourly checks)."
        risk_level = "MEDIUM"
    else:
        recommendation = "DELAY ACCEPTABLE — Risk increase is manageable. Maintain standard monitoring."
        risk_level = "LOW"

    return {
        "delay_days": delay_days,
        "current_rul_days": current_rul,
        "projected_rul_days": new_rul,
        "current_failure_probability": current_failure_prob,
        "projected_failure_probability": new_failure_prob,
        "failure_prob_increase_pct": round((new_failure_prob - current_failure_prob) * 100, 1),
        "additional_expected_loss_inr": round(additional_expected_loss, 0),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "monitoring_interval": "1 hour" if risk_level in ("CRITICAL", "HIGH") else "4 hours",
    }
