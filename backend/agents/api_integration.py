"""
API Integration for Dynamic Health Calculations

Bridges the dynamic health engine with FastAPI endpoints.
Maintains backward compatibility while adding new endpoints for advanced analytics.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from agents.dynamic_health import (
    compute_dynamic_health_index,
    compute_alert_level,
    compute_maintenance_schedule,
    get_season,
)
from agents.maintenance_optimizer import (
    calculate_maintenance_roi,
    calculate_total_maintenance_cost,
    MaintenanceScheduleOptimizer,
    generate_maintenance_report,
)
from agents.rul_predictor import EQUIPMENT_PARAMS
from data.sensor_history import generate_history, get_trend_summary


def get_equipment_health_detailed(
    equipment_id: str,
    sensor_data: Dict[str, Any],
    equipment_type: str = "pump",
    sensor_history: Optional[List[Dict]] = None,
    last_maintenance: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Get comprehensive health assessment using dynamic calculation.
    
    Returns all metrics needed for UI rendering and decision making.
    """
    
    # Generate sensor history if not provided
    if sensor_history is None:
        sensor_history = generate_history(equipment_id, hours=720)
    
    # Compute dynamic health
    dynamic_health = compute_dynamic_health_index(
        sensor_data,
        equipment_type,
        sensor_history
    )
    
    health_index = dynamic_health["health_index"]
    
    # Compute alert level dynamically
    alert_level = compute_alert_level(
        health_index,
        dynamic_health["component_scores"],
        dynamic_health["trend_velocities"],
        equipment_type
    )
    
    # Estimate RUL and failure probability
    rul_days = max(0.5, health_index / 100.0 * 180)  # Simple RUL model
    failure_prob = 1.0 - (health_index / 100.0) ** 2
    
    # Get maintenance schedule
    maintenance_schedule = compute_maintenance_schedule(
        equipment_id,
        equipment_type,
        health_index,
        dynamic_health["health_status"],
        last_maintenance
    )
    
    # Calculate ROI
    roi = calculate_maintenance_roi(
        equipment_type,
        health_index,
        rul_days * 24,
        maintenance_type="planned"
    )
    
    # Get trend summary
    trend_summary = get_trend_summary(equipment_id, hours=168)
    
    return {
        # Core metrics
        "equipment_id": equipment_id,
        "equipment_type": equipment_type,
        "timestamp": datetime.now().isoformat(),
        "season": dynamic_health["season"],
        
        # Health assessment
        "health_index": health_index,
        "health_status": dynamic_health["health_status"],
        "alert_level": alert_level,
        "failure_probability": round(failure_prob, 3),
        
        # Component details
        "component_scores": {
            k: {
                "value": v["value"],
                "health": v["health"],
                "state": v["state"],
                "trend_velocity": dynamic_health["trend_velocities"].get(k, 0),
            }
            for k, v in dynamic_health["component_scores"].items()
        },
        
        # Degradation analysis
        "degradation_rate": dynamic_health["degradation_rate_classification"],
        "adaptive_weights": dynamic_health["adaptive_weights"],
        
        # RUL and maintenance
        "predicted_rul_days": round(rul_days, 1),
        "maintenance_schedule": maintenance_schedule,
        
        # Financial analysis
        "cost_analysis": {
            "maintenance_cost": roi["maintenance_cost"],
            "expected_failure_cost": roi["expected_failure_cost"],
            "roi_value": roi["roi_value"],
            "roi_ratio": roi["roi_ratio"],
        },
        "maintenance_recommendation": roi["recommendation"],
        
        # Trends
        "sensor_trends": trend_summary.get("sensor_trends", {}),
        
        # Recommendations
        "recommendations": dynamic_health["recommendations"],
    }


def get_fleet_health_status(
    fleet_data: Dict[str, Dict],
    sensor_data_map: Dict[str, Dict]
) -> Dict[str, Any]:
    """
    Get fleet-wide health status with prioritized maintenance queue.
    """
    
    equipment_health = []
    
    for eq_id, eq_info in fleet_data.items():
        if eq_id not in sensor_data_map:
            continue
        
        health_detail = get_equipment_health_detailed(
            eq_id,
            sensor_data_map[eq_id],
            eq_info.get("type", "pump")
        )
        
        # Add criticality for prioritization
        health_detail["criticality"] = eq_info.get("criticality", "Medium")
        health_detail["location"] = eq_info.get("location", "Unknown")
        
        equipment_health.append(health_detail)
    
    # Sort by criticality of alert level
    alert_severity = {"EMERGENCY": 4, "CRITICAL": 3, "WARNING": 2, "NORMAL": 1}
    equipment_health.sort(
        key=lambda x: (
            alert_severity.get(x["alert_level"], 0),
            100 - x["health_index"]
        ),
        reverse=True
    )
    
    # Create maintenance optimizer
    fleet_for_optimizer = [
        {
            "equipment_id": eq["equipment_id"],
            "equipment_type": eq["equipment_type"],
            "health_index": eq["health_index"],
            "predicted_rul_days": eq["predicted_rul_days"],
            "location": eq.get("location", "Unknown"),
            "criticality": eq.get("criticality", "Medium"),
        }
        for eq in equipment_health
    ]
    
    optimizer = MaintenanceScheduleOptimizer(fleet_for_optimizer)
    maintenance_queue = optimizer.prioritize_maintenance_queue(
        maintenance_capacity_hours_per_day=8,
        days_planning_horizon=30
    )
    
    batch_opportunities = optimizer.suggest_batch_maintenance()
    
    # Calculate fleet-wide metrics
    avg_health = sum(eq["health_index"] for eq in equipment_health) / max(len(equipment_health), 1)
    critical_count = sum(1 for eq in equipment_health if eq["alert_level"] in ["CRITICAL", "EMERGENCY"])
    
    return {
        "timestamp": datetime.now().isoformat(),
        "fleet_summary": {
            "total_equipment": len(equipment_health),
            "average_health_index": round(avg_health, 1),
            "equipment_in_critical_state": critical_count,
            "equipment_requiring_maintenance_30d": len(maintenance_queue),
        },
        "equipment_status": equipment_health,
        "maintenance_queue": maintenance_queue,
        "batch_maintenance_opportunities": batch_opportunities,
        "season": get_season(),
    }


def get_maintenance_plan(
    fleet_data: Dict[str, Dict],
    sensor_data_map: Dict[str, Dict],
    days_horizon: int = 30,
) -> Dict[str, Any]:
    """
    Get comprehensive maintenance plan for the fleet.
    """
    
    # Get fleet health
    fleet_status = get_fleet_health_status(fleet_data, sensor_data_map)
    
    # Detailed maintenance reports
    maintenance_reports = []
    for eq in fleet_status["equipment_status"]:
        report = generate_maintenance_report(eq)
        maintenance_reports.append(report)
    
    # Calculate total budget impact
    total_planned_cost = sum(r["cost_analysis"]["planned_maintenance_cost"] for r in maintenance_reports)
    total_roi_opportunity = sum(r["cost_analysis"]["roi_value"] for r in maintenance_reports if r["cost_analysis"]["roi_value"] > 0)
    
    # Group by priority
    emergency = [r for r in maintenance_reports if r["maintenance_recommendation"] == "MAINTAIN_NOW"]
    soon = [r for r in maintenance_reports if r["maintenance_recommendation"] == "MAINTAIN_SOON"]
    monitor = [r for r in maintenance_reports if r["maintenance_recommendation"] == "MONITOR"]
    
    return {
        "plan_date": datetime.now().isoformat(),
        "planning_horizon_days": days_horizon,
        "summary": {
            "total_equipment_requiring_maintenance": len(emergency) + len(soon),
            "equipment_in_emergency_state": len(emergency),
            "equipment_requiring_planned_maintenance": len(soon),
            "equipment_to_monitor": len(monitor),
        },
        "financial_summary": {
            "total_planned_maintenance_cost": round(total_planned_cost, 0),
            "total_roi_opportunity": round(total_roi_opportunity, 0),
            "average_roi_per_equipment": round(total_roi_opportunity / max(len(maintenance_reports), 1), 0),
        },
        "maintenance_by_priority": {
            "emergency": [
                {
                    "equipment_id": r["equipment_id"],
                    "health_index": r["health_index"],
                    "recommended_action": r["schedule_recommendation"]["maintenance_type"],
                }
                for r in emergency
            ],
            "soon": [
                {
                    "equipment_id": r["equipment_id"],
                    "health_index": r["health_index"],
                    "recommended_action": r["schedule_recommendation"]["maintenance_type"],
                }
                for r in soon
            ],
            "monitor": [
                {
                    "equipment_id": r["equipment_id"],
                    "health_index": r["health_index"],
                }
                for r in monitor
            ],
        },
        "all_maintenance_reports": maintenance_reports,
    }


def get_what_if_analysis(
    equipment_id: str,
    equipment_type: str,
    sensor_data: Dict[str, Any],
    delay_days: int,
    sensor_history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Analyze impact of delaying maintenance.
    """
    
    # Current state
    current = get_equipment_health_detailed(
        equipment_id,
        sensor_data,
        equipment_type,
        sensor_history
    )
    
    # Project future state with degradation
    degradation_per_day = 0.5  # 0.5% per day typical degradation
    projected_health = max(0, current["health_index"] - (degradation_per_day * delay_days))
    
    # Get costs at different maintenance windows
    cost_now = calculate_total_maintenance_cost(equipment_type, "planned", 8)
    cost_delayed = calculate_total_maintenance_cost(equipment_type, "planned", 8)
    cost_emergency = calculate_total_maintenance_cost(equipment_type, "emergency", 4, is_emergency=True)
    
    # Calculate financial impact
    base_production_loss = 8300000 if equipment_type == "furnace" else 3700000  # Daily loss
    additional_loss_from_delay = (base_production_loss / 24) * delay_days * (1 + delay_days / 30)  # Accelerating
    
    return {
        "equipment_id": equipment_id,
        "scenario_delay_days": delay_days,
        "current_state": {
            "health_index": current["health_index"],
            "alert_level": current["alert_level"],
            "maintenance_cost_if_done_now": cost_now["total_cost"],
        },
        "projected_state": {
            "health_index": round(projected_health, 1),
            "alert_level": "EMERGENCY" if projected_health < 40 else "CRITICAL" if projected_health < 60 else "WARNING",
            "maintenance_cost_if_done_later": cost_delayed["total_cost"],
            "risk_of_failure": round(1.0 - (projected_health / 100) ** 2, 3),
        },
        "impact_analysis": {
            "health_degradation": round(current["health_index"] - projected_health, 1),
            "additional_production_loss_estimate": round(additional_loss_from_delay, 0),
            "emergency_repair_cost_if_fails": cost_emergency["total_cost"],
            "financial_impact_of_delay": round(additional_loss_from_delay - cost_now["total_cost"], 0),
        },
        "recommendation": (
            "Maintain now - delay risk is too high"
            if projected_health < 60 else
            "Consider maintaining before delay expires"
            if projected_health < 75 else
            "Delay acceptable with monitoring"
        ),
    }
