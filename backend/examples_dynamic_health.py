"""
Example Usage and Tests for Dynamic Asset Health & Maintenance System

This file demonstrates how to use the dynamic health calculation engine
with real examples from Stelos equipment data.
"""

import json
from datetime import datetime, timedelta
from agents.api_integration import (
    get_equipment_health_detailed,
    get_fleet_health_status,
    get_maintenance_plan,
    get_what_if_analysis,
)
from agents.dynamic_health import (
    compute_dynamic_health_index,
    compute_alert_level,
    compute_maintenance_schedule,
)
from agents.maintenance_optimizer import (
    calculate_maintenance_roi,
    MaintenanceScheduleOptimizer,
)
from data.sensor_history import generate_history


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 1: Individual Equipment Analysis
# ─────────────────────────────────────────────────────────────────

def example_equipment_health_analysis():
    """
    Analyze health of a single piece of equipment with full diagnostic report.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Individual Equipment Health Analysis")
    print("="*80)
    
    # Pump in warning state with rising temperature
    sensor_data = {
        "temperature": 82.0,      # Above nominal 65°C
        "vibration": 0.45,        # Normal range
        "pressure": 95.0,         # Slightly low
        "oil_temp": 58.0,         # Normal
        "motor_current": 48.0,    # Slightly elevated
    }
    
    # Get health analysis
    health = get_equipment_health_detailed(
        equipment_id="Pump-B",
        sensor_data=sensor_data,
        equipment_type="pump",
        sensor_history=generate_history("Pump-B", hours=720)
    )
    
    print(f"\n📊 Equipment: {health['equipment_id']}")
    print(f"   Type: {health['equipment_type'].upper()}")
    print(f"   Location: Blast Furnace #3")
    print(f"   Timestamp: {health['timestamp']}")
    
    print(f"\n💚 Health Status:")
    print(f"   Health Index: {health['health_index']}% ({health['health_status']})")
    print(f"   Alert Level: {health['alert_level']}")
    print(f"   Failure Probability: {health['failure_probability']*100:.1f}%")
    print(f"   Predicted RUL: {health['predicted_rul_days']} days")
    print(f"   Degradation Rate: {health['degradation_rate_classification']}")
    
    print(f"\n🔍 Component Scores:")
    for sensor, data in health['component_scores'].items():
        print(f"   {sensor:15} | Value: {data['value']:6} | Health: {data['health']:5.1f}% | State: {data['state']:10} | Trend: {data['trend_velocity']:+6.2f}%/day")
    
    print(f"\n💰 Financial Analysis:")
    print(f"   Maintenance Cost:     ₹{health['cost_analysis']['maintenance_cost']:,}")
    print(f"   Expected Failure Cost: ₹{health['cost_analysis']['expected_failure_cost']:,}")
    print(f"   ROI Value:            ₹{health['cost_analysis']['roi_value']:,}")
    print(f"   ROI Ratio:            {health['cost_analysis']['roi_ratio']:.2f}x")
    
    print(f"\n⚙️  Maintenance Recommendation: {health['maintenance_recommendation']}")
    schedule = health['maintenance_schedule']
    print(f"   Next Maintenance: {schedule['maintenance_type'].upper()}")
    print(f"   Urgency: {schedule['urgency_level'].upper()}")
    print(f"   Recommended Within: {schedule['days_until_recommended']} days")
    
    print(f"\n📈 Adaptive Weights (Equipment-Specific):")
    for sensor, weight in health['adaptive_weights'].items():
        print(f"   {sensor:15} {weight*100:5.1f}%")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(health['recommendations'], 1):
        print(f"   {i}. {rec}")


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 2: Fleet-Wide Status and Prioritization
# ─────────────────────────────────────────────────────────────────

def example_fleet_status():
    """
    Get fleet-wide health status with maintenance prioritization.
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Fleet-Wide Status & Maintenance Prioritization")
    print("="*80)
    
    # Simulated fleet data
    FLEET = {
        "Pump-B": {"type": "pump", "location": "Blast Furnace #3", "criticality": "Critical", "base_health": 25.0},
        "Pump-A": {"type": "pump", "location": "Blast Furnace #2", "criticality": "High", "base_health": 82.0},
        "Conveyor-B": {"type": "conveyor", "location": "Raw Material Yard", "criticality": "High", "base_health": 70.0},
        "Cooling-Fan-4": {"type": "fan", "location": "Sinter Plant", "criticality": "Medium", "base_health": 87.0},
        "Blast-Furnace": {"type": "furnace", "location": "Blast Furnace #1", "criticality": "Critical", "base_health": 68.0},
    }
    
    # Generate sensor data for each
    def simulate_sensor_data(eq_id, base_health):
        degradation = (100 - base_health) / 100
        return {
            "temperature": 65 + degradation * 30 + (hash(eq_id) % 10 - 5),
            "vibration": 0.30 + degradation * 0.60 + ((hash(eq_id) % 20 - 10) / 1000),
            "pressure": 100 - degradation * 15,
            "oil_temp": 52 + degradation * 20,
            "motor_current": 42 + degradation * 8,
        }
    
    fleet_sensor_data = {
        eq_id: simulate_sensor_data(eq_id, info["base_health"])
        for eq_id, info in FLEET.items()
    }
    
    # Get fleet status
    fleet_status = get_fleet_health_status(FLEET, fleet_sensor_data)
    
    print(f"\n📊 Fleet Summary ({fleet_status['timestamp']}):")
    print(f"   Total Equipment: {fleet_status['fleet_summary']['total_equipment']}")
    print(f"   Average Health: {fleet_status['fleet_summary']['average_health_index']}%")
    print(f"   Critical Equipment: {fleet_status['fleet_summary']['equipment_in_critical_state']}")
    print(f"   Needs Maintenance (30d): {fleet_status['fleet_summary']['equipment_requiring_maintenance_30d']}")
    print(f"   Season: {fleet_status['season'].upper()}")
    
    print(f"\n⚠️  Equipment Status (Ranked by Priority):")
    print(f"   {'Rank':<5} {'Equipment':<15} {'Type':<10} {'Health':<8} {'Alert':<12} {'Urgency':<12} {'Days':<6}")
    print(f"   {'-'*75}")
    
    for i, eq in enumerate(fleet_status['equipment_status'][:8], 1):
        maintenance = eq['maintenance_schedule']
        print(f"   {i:<5} {eq['equipment_id']:<15} {eq['equipment_type']:<10} {eq['health_index']:>6.1f}% {eq['alert_level']:<12} {maintenance['urgency_level']:<12} {maintenance['days_until_recommended']:<6.1f}")
    
    print(f"\n📅 Maintenance Queue (Next 30 Days):")
    for item in fleet_status['maintenance_queue'][:5]:
        print(f"   {item['priority_rank']}. {item['equipment_id']:<15} | {item['maintenance_type']:>8} | {item['downtime_hours']:>4}h | Scheduled: {item['scheduled_date']}")
    
    if fleet_status['batch_maintenance_opportunities']:
        print(f"\n🔗 Batch Maintenance Opportunities:")
        for batch in fleet_status['batch_maintenance_opportunities']:
            print(f"   Location: {batch['location']}")
            print(f"   Equipment: {', '.join(batch['equipment_ids'])}")
            print(f"   Efficiency Gain: {batch['efficiency_gain']} (vs separate maintenance)")


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 3: Comprehensive 30-Day Maintenance Plan
# ─────────────────────────────────────────────────────────────────

def example_maintenance_plan():
    """
    Generate comprehensive 30-day maintenance plan with financial analysis.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: 30-Day Maintenance Plan & Financial Analysis")
    print("="*80)
    
    FLEET = {
        "Pump-B": {"type": "pump", "location": "Blast Furnace #3", "criticality": "Critical", "base_health": 25.0},
        "Pump-A": {"type": "pump", "location": "Blast Furnace #2", "criticality": "High", "base_health": 82.0},
        "Conveyor-B": {"type": "conveyor", "location": "Raw Material Yard", "criticality": "High", "base_health": 70.0},
        "Cooling-Fan-4": {"type": "fan", "location": "Sinter Plant", "criticality": "Medium", "base_health": 87.0},
        "Blast-Furnace": {"type": "furnace", "location": "Blast Furnace #1", "criticality": "Critical", "base_health": 68.0},
    }
    
    def simulate_sensor_data(eq_id, base_health):
        degradation = (100 - base_health) / 100
        return {
            "temperature": 65 + degradation * 30,
            "vibration": 0.30 + degradation * 0.60,
            "pressure": 100 - degradation * 15,
            "oil_temp": 52 + degradation * 20,
            "motor_current": 42 + degradation * 8,
        }
    
    fleet_sensor_data = {eq_id: simulate_sensor_data(eq_id, info["base_health"]) for eq_id, info in FLEET.items()}
    
    plan = get_maintenance_plan(FLEET, fleet_sensor_data, days_horizon=30)
    
    print(f"\n📋 Plan Summary (Horizon: {plan['planning_horizon_days']} days):")
    print(f"   Equipment Requiring Maintenance: {plan['summary']['total_equipment_requiring_maintenance']}")
    print(f"   Emergency (Urgent): {plan['summary']['equipment_in_emergency_state']}")
    print(f"   Planned (Soon): {plan['summary']['equipment_requiring_planned_maintenance']}")
    print(f"   Monitor: {plan['summary']['equipment_to_monitor']}")
    
    print(f"\n💰 Financial Summary:")
    print(f"   Total Maintenance Budget: ₹{plan['financial_summary']['total_planned_maintenance_cost']:,}")
    print(f"   Total ROI Opportunity: ₹{plan['financial_summary']['total_roi_opportunity']:,}")
    print(f"   Average ROI per Equipment: ₹{plan['financial_summary']['average_roi_per_equipment']:,}")
    
    print(f"\n🚨 EMERGENCY (Maintain Immediately):")
    if plan['maintenance_by_priority']['emergency']:
        for eq in plan['maintenance_by_priority']['emergency']:
            print(f"   • {eq['equipment_id']:<20} Health: {eq['health_index']:>6.1f}% | Type: {eq['recommended_action']}")
    else:
        print("   None")
    
    print(f"\n⚠️  PLANNED (Maintain This Month):")
    if plan['maintenance_by_priority']['soon']:
        for eq in plan['maintenance_by_priority']['soon']:
            print(f"   • {eq['equipment_id']:<20} Health: {eq['health_index']:>6.1f}% | Type: {eq['recommended_action']}")
    else:
        print("   None")
    
    print(f"\n📊 MONITOR:")
    if plan['maintenance_by_priority']['monitor']:
        for eq in plan['maintenance_by_priority']['monitor'][:5]:
            print(f"   • {eq['equipment_id']:<20} Health: {eq['health_index']:>6.1f}%")
    else:
        print("   All equipment scheduled for maintenance")


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 4: What-If Analysis (Impact of Delay)
# ─────────────────────────────────────────────────────────────────

def example_what_if_analysis():
    """
    Analyze impact of delaying maintenance by different periods.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: What-If Analysis - Impact of Maintenance Delay")
    print("="*80)
    
    sensor_data = {
        "temperature": 85.0,
        "vibration": 0.65,
        "pressure": 95.0,
        "oil_temp": 58.0,
        "motor_current": 50.0,
    }
    
    # Analyze different delay scenarios
    delay_scenarios = [0, 3, 7, 10, 14]
    
    print(f"\n📊 Pump-B - Delay Impact Analysis")
    print(f"{'Delay (days)':<15} {'Health %':<12} {'Alert Level':<15} {'Failure Risk':<15} {'Production Loss':<20} {'Recommendation':<30}")
    print(f"{'-'*105}")
    
    for delay in delay_scenarios:
        whatif = get_what_if_analysis(
            equipment_id="Pump-B",
            equipment_type="pump",
            sensor_data=sensor_data,
            delay_days=delay,
            sensor_history=generate_history("Pump-B", hours=720)
        )
        
        projected = whatif['projected_state']
        impact = whatif['impact_analysis']
        
        print(f"{delay:<15} {projected['health_index']:>10.1f}% {projected['alert_level']:<15} {whatif['current_state'] if delay == 0 else f\"{projected['risk_of_failure']*100:.0f}%\":<15} ₹{impact['additional_production_loss_estimate']:>18,.0f} {whatif['recommendation']:<30}")


# ─────────────────────────────────────────────────────────────────
# EXAMPLE 5: ROI Calculation for Different Scenarios
# ─────────────────────────────────────────────────────────────────

def example_roi_analysis():
    """
    Compare ROI for different equipment types and health states.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: ROI Analysis Across Equipment Types")
    print("="*80)
    
    scenarios = [
        ("pump", 45, "low_health"),
        ("furnace", 55, "degrading"),
        ("conveyor", 70, "stable"),
        ("fan", 65, "warning"),
        ("mill", 50, "critical"),
    ]
    
    print(f"\n{'Equipment':<15} {'Health':<10} {'Scenario':<15} {'Maint. Cost':<15} {'Failure Cost':<15} {'ROI Value':<15} {'Recommendation':<20}")
    print(f"{'-'*110}")
    
    for eq_type, health, scenario in scenarios:
        hours_until_failure = (health / 100) * 200 * 24  # Rough estimate
        
        roi = calculate_maintenance_roi(
            equipment_type=eq_type,
            health_index=health,
            hours_until_probable_failure=hours_until_failure,
            maintenance_type="planned"
        )
        
        print(f"{eq_type:<15} {health:<10.0f} {scenario:<15} ₹{roi['maintenance_cost']:<14,.0f} ₹{roi['expected_failure_cost']:<14,.0f} ₹{roi['roi_value']:<14,.0f} {roi['recommendation']:<20}")


# ─────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Stelos Dynamic Asset Health & Maintenance System")
    print("Example Usage & Demonstrations")
    print("="*80)
    
    try:
        example_equipment_health_analysis()
        example_fleet_status()
        example_maintenance_plan()
        example_what_if_analysis()
        example_roi_analysis()
        
        print("\n" + "="*80)
        print("✅ All examples completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
