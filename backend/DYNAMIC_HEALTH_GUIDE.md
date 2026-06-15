# Dynamic Asset Health & Maintenance Calculation System

## Overview

The Stelos system now features a **dynamic, adaptive asset health and maintenance calculation engine** that goes far beyond static thresholds. The system makes intelligent, context-aware decisions by continuously adapting to:

- **Equipment type & operational context**
- **Real-time degradation trends** (velocity of decline)
- **Production impact & criticality**
- **Historical patterns & seasonality**
- **Optimal maintenance windows**

## Key Innovations

### 1. **Adaptive Sensor Weights** 🔄
Traditional systems use fixed weights. Stelos adjusts weights based on:
- **Equipment type**: Furnaces weight temperature higher; conveyors weight vibration higher
- **Health state**: As equipment degrades, critical sensors get higher weight
- **Seasonal variations**: Summer emphasizes temperature; winter emphasizes vibration
- **Degradation trends**: Sensors showing rapid decline get elevated priority

**Example**: A pump's temperature weight changes from 40% (normal) → 45% (summer) → 50% (critical state)

### 2. **Dynamic Alert Thresholds** ⚠️
Thresholds vary per equipment type and operating conditions:

```yaml
Pump Normal:      Temp < 78°C  (Warning threshold)
Pump Summer:      Temp < 73°C  (More aggressive)
Pump Degraded:    Temp < 65°C  (Even more aggressive)

Furnace Normal:   Temp < 200°C (Different baseline!)
Furnace Summer:   Temp < 190°C
Furnace Critical: Temp < 180°C
```

### 3. **Trend-Based Health Scoring** 📈
The system analyzes degradation velocity:
- **Slow** (<0.2% per day): Normal aging
- **Normal** (0.2-0.5% per day): Expected decline
- **Fast** (0.5-1.2% per day): Accelerated degradation, urgent action
- **Critical** (>1.2% per day): Emergency state

### 4. **Cost-Benefit Maintenance Optimization** 💰
Before recommending maintenance, calculates:
- Direct maintenance cost
- Production loss during downtime
- Expected failure cost if delayed
- Secondary damage risk
- Return on investment (ROI)

**Example Analysis**:
- Maintenance cost now: ₹10L
- Production loss (8hr maintenance): ₹30L
- **Total: ₹40L**
- Expected failure cost if delayed: ₹200L
- **ROI: Save ₹160L by maintaining now** ✓

### 5. **Equipment-Specific Intelligence** 🏭
Different equipment has vastly different operational profiles:

| Equipment | Critical Sensor | Nominal RUL | Production Loss/hr | Emergency Cost |
|-----------|-----------------|-------------|-------------------|---|
| **Pump** | Vibration | 180d | ₹37L | ₹22L |
| **Fan** | Vibration | 270d | ₹4L | ₹3L |
| **Conveyor** | Vibration | 365d | ₹8L | ₹6L |
| **Furnace** | Temperature | 90d | ₹83L | ₹1.5Cr |
| **Mill** | Vibration | 120d | ₹58L | ₹45L |

### 6. **Maintenance Schedule Optimization** 📅
Finds optimal maintenance windows considering:
- Health urgency (emergency vs. routine)
- Production schedule (schedule during low-production periods)
- Maintenance team capacity (spreads load)
- Equipment interdependencies (batch related equipment)
- Spare parts availability

### 7. **Fleet-Level Coordination** 🚀
When multiple equipment needs maintenance:
- **Batch maintenance**: Group repairs in same location to reduce total downtime
- **Capacity planning**: Spread maintenance across available team capacity
- **Priority ranking**: Order by ROI and failure probability

## Architecture

### Core Modules

```
backend/agents/
├── dynamic_health.py          # Core health calculation engine
├── maintenance_optimizer.py   # Cost/ROI analysis & scheduling
├── api_integration.py         # FastAPI bridges & helpers
├── rul_predictor.py          # (existing) RUL estimation
└── anomaly_detector.py        # (existing) Sensor anomaly detection
```

## Usage Examples

### 1. Get Detailed Equipment Health (Dynamic)

```python
from agents.api_integration import get_equipment_health_detailed
from data.sensor_history import generate_history

# Current sensor readings
sensor_data = {
    "temperature": 82.0,
    "vibration": 0.45,
    "pressure": 98.5,
    "oil_temp": 55.0,
    "motor_current": 48.0
}

# Get sensor history for trend analysis
history = generate_history("Pump-A", hours=720)

# Compute dynamic health
health = get_equipment_health_detailed(
    equipment_id="Pump-A",
    sensor_data=sensor_data,
    equipment_type="pump",
    sensor_history=history
)

print(f"Health Index: {health['health_index']}%")
print(f"Status: {health['health_status']}")
print(f"Alert Level: {health['alert_level']}")
print(f"Degradation Rate: {health['degradation_rate']}")
print(f"Maintenance Recommendation: {health['maintenance_recommendation']}")
print(f"Cost ROI: Save ₹{health['cost_analysis']['roi_value']} by maintaining now")
```

**Output Example**:
```
Health Index: 62.4%
Status: FAIR
Alert Level: WARNING
Degradation Rate: fast
Maintenance Recommendation: MAINTAIN_SOON
Cost ROI: Save ₹125,000 by maintaining now

Component Details:
- Temperature: 82.0°C (FAIR state, +1.2%/day rising)
- Vibration: 0.45 mm/s (GOOD state, stable)
- Pressure: 98.5 PSI (EXCELLENT state, stable)

Recommendations:
1. ⚠ Temperature deteriorating rapidly (+1.2%/day). Plan maintenance within 7 days.
2. Focus inspection on temperature sensor - may indicate bearing wear or coolant issue.
3. Health declining. Schedule maintenance before next planned downtime.
```

### 2. Get Fleet-Wide Health Status

```python
from agents.api_integration import get_fleet_health_status

# Simulated sensor data for all equipment
fleet_sensor_data = {
    "Pump-A": {"temperature": 78.0, "vibration": 0.32, ...},
    "Pump-B": {"temperature": 88.0, "vibration": 0.58, ...},
    "Furnace": {"temperature": 195.0, "vibration": 0.25, ...},
    # ... more equipment
}

# Get fleet status with maintenance prioritization
fleet_status = get_fleet_health_status(FLEET, fleet_sensor_data)

print(f"Fleet Average Health: {fleet_status['fleet_summary']['average_health_index']}%")
print(f"Critical Equipment: {fleet_status['fleet_summary']['equipment_in_critical_state']}")

# Prioritized maintenance queue (considering ROI & urgency)
for item in fleet_status['maintenance_queue'][:5]:
    print(f"\n{item['priority_rank']}. {item['equipment_id']} ({item['equipment_type']})")
    print(f"   Health: {item['health_index']}%")
    print(f"   Scheduled: {item['scheduled_date']}")
    print(f"   Duration: {item['maintenance_duration_hours']}h")

# Batch maintenance opportunities
for batch in fleet_status['batch_maintenance_opportunities']:
    print(f"\nBatch Opportunity at {batch['location']}")
    print(f"   Equipment: {batch['equipment_ids']}")
    print(f"   Total Downtime: {batch['total_downtime_hours']}h vs {len(batch['equipment_ids']) * 4}h separately")
    print(f"   Efficiency Gain: {batch['efficiency_gain']}")
```

### 3. Calculate Maintenance ROI

```python
from agents.maintenance_optimizer import calculate_maintenance_roi

# Equipment status
equipment_type = "pump"
health_index = 55.0  # Critical state
hours_until_failure = 48.0

# Calculate ROI
roi = calculate_maintenance_roi(
    equipment_type=equipment_type,
    health_index=health_index,
    hours_until_probable_failure=hours_until_failure,
    maintenance_type="planned",
    downtime_hours=8
)

print(f"Maintenance Cost Now: ₹{roi['maintenance_cost']}")
print(f"Expected Failure Cost: ₹{roi['expected_failure_cost']}")
print(f"ROI Value (Savings): ₹{roi['roi_value']}")
print(f"ROI Ratio: {roi['roi_ratio']}x")
print(f"Recommendation: {roi['recommendation']}")
```

### 4. What-If Analysis (Delay Impact)

```python
from agents.api_integration import get_what_if_analysis

# Analyze impact of delaying maintenance by 10 days
whatif = get_what_if_analysis(
    equipment_id="Pump-B",
    equipment_type="pump",
    sensor_data=sensor_data,
    delay_days=10,
    sensor_history=history
)

print(f"Current Health: {whatif['current_state']['health_index']}%")
print(f"After 10-day Delay: {whatif['projected_state']['health_index']}%")
print(f"Health Degradation: {whatif['impact_analysis']['health_degradation']}%")
print(f"Additional Production Loss: ₹{whatif['impact_analysis']['additional_production_loss_estimate']}")
print(f"Recommendation: {whatif['recommendation']}")
```

### 5. Comprehensive Maintenance Plan

```python
from agents.api_integration import get_maintenance_plan

plan = get_maintenance_plan(
    fleet_data=FLEET,
    sensor_data_map=fleet_sensor_data,
    days_horizon=30
)

print(f"\n30-Day Maintenance Plan")
print(f"=======================")
print(f"Equipment Requiring Maintenance: {plan['summary']['total_equipment_requiring_maintenance']}")
print(f"Emergency (Urgent): {plan['summary']['equipment_in_emergency_state']}")
print(f"Planned (Soon): {plan['summary']['equipment_requiring_planned_maintenance']}")
print(f"Total Budget: ₹{plan['financial_summary']['total_planned_maintenance_cost']}")
print(f"Total ROI Opportunity: ₹{plan['financial_summary']['total_roi_opportunity']}")

# Emergency maintenance
if plan['maintenance_by_priority']['emergency']:
    print(f"\n🚨 EMERGENCY (Maintain Immediately):")
    for eq in plan['maintenance_by_priority']['emergency']:
        print(f"   • {eq['equipment_id']} (Health: {eq['health_index']}%)")

# Scheduled maintenance
if plan['maintenance_by_priority']['soon']:
    print(f"\n⚠️  SCHEDULED (Maintain This Month):")
    for eq in plan['maintenance_by_priority']['soon']:
        print(f"   • {eq['equipment_id']} (Health: {eq['health_index']}%)")
```

## API Endpoints (To Be Added to main.py)

```python
# In main.py, add these endpoints:

@app.post("/api/v2/equipment/{equipment_id}/health-detailed")
async def get_equipment_health_v2(equipment_id: str):
    """
    Get comprehensive equipment health with dynamic calculation.
    Returns detailed analysis with adaptive weights, trends, and recommendations.
    """
    sensor_data = _simulate_sensor_data(equipment_id)
    history = generate_history(equipment_id, hours=720)
    eq_type = FLEET.get(equipment_id, {}).get("type", "pump")
    
    return get_equipment_health_detailed(
        equipment_id=equipment_id,
        sensor_data=sensor_data,
        equipment_type=eq_type,
        sensor_history=history
    )


@app.get("/api/v2/fleet/status")
async def get_fleet_status_v2():
    """
    Get fleet-wide status with prioritized maintenance queue.
    Includes ROI analysis, batch opportunities, and optimization.
    """
    sensor_data_map = {
        eq_id: _simulate_sensor_data(eq_id)
        for eq_id in FLEET.keys()
    }
    
    return get_fleet_health_status(FLEET, sensor_data_map)


@app.get("/api/v2/maintenance/plan")
async def get_maintenance_plan_v2(days_horizon: int = 30):
    """
    Get comprehensive 30-day maintenance plan with ROI analysis.
    Groups equipment by priority, suggests batch maintenance, calculates savings.
    """
    sensor_data_map = {
        eq_id: _simulate_sensor_data(eq_id)
        for eq_id in FLEET.keys()
    }
    
    return get_maintenance_plan(FLEET, sensor_data_map, days_horizon)


@app.post("/api/v2/equipment/{equipment_id}/what-if")
async def what_if_delay_v2(equipment_id: str, delay_days: int):
    """
    Analyze impact of delaying maintenance.
    Shows health degradation, production loss, and cost implications.
    """
    sensor_data = _simulate_sensor_data(equipment_id)
    history = generate_history(equipment_id, hours=720)
    eq_type = FLEET.get(equipment_id, {}).get("type", "pump")
    
    return get_what_if_analysis(
        equipment_id=equipment_id,
        equipment_type=eq_type,
        sensor_data=sensor_data,
        delay_days=delay_days,
        sensor_history=history
    )
```

## Configuration & Customization

### Add Custom Equipment Type

```python
# In dynamic_health.py, add to EQUIPMENT_PROFILES:

EQUIPMENT_PROFILES["compressor"] = {
    "base_weights": {"temperature": 0.35, "vibration": 0.40, "pressure": 0.20, "oil_temp": 0.05},
    "seasonal_adjustments": {
        "summer": {"temperature": 0.40, "vibration": 0.35},
        "winter": {"temperature": 0.30, "vibration": 0.45},
    },
    "degradation_curves": {
        "slow": 0.15,
        "normal": 0.35,
        "fast": 0.8,
        "critical": 1.8,
    },
    "threshold_ranges": {
        "temperature": {"low": 50, "nominal": 65, "warn": 78, "critical": 85, "trip": 95},
        "vibration": {"low": 0.15, "nominal": 0.30, "warn": 0.50, "critical": 0.70, "trip": 1.0},
        "pressure": {"low": 80, "nominal": 100, "warn_low": 85, "warn_high": 115, "critical_high": 125},
    },
    "maintenance_windows": {
        "routine": 45,
        "planned": 90,
        "emergency": 1.5,
    }
}
```

### Adjust Cost Parameters

```python
# In maintenance_optimizer.py, update EQUIPMENT_COSTS:

EQUIPMENT_COSTS["compressor"] = {
    "production_loss_per_hour": 2000000,    # ₹20L/hr
    "planned_maintenance_cost": 300000,     # ₹3L
    "major_maintenance_cost": 1000000,      # ₹10L
    "emergency_repair_cost": 1500000,       # ₹15L
    "spare_lead_time_days": 5,
}
```

## Key Features Implemented

✅ **Adaptive Health Calculation**
- Dynamic sensor weights based on equipment type, health state, and season
- Context-aware threshold normalization
- Bidirectional penalty for high and low deviations

✅ **Trend Analysis**
- Degradation velocity calculation (% per day)
- Trend-based alert recommendations
- Acceleration detection for rapid failures

✅ **Financial Analysis**
- Production loss estimation during downtime
- Emergency repair cost modeling
- ROI calculation (maintenance now vs. failure later)
- Cost-benefit decision support

✅ **Maintenance Optimization**
- Urgency-based prioritization
- Equipment batching for efficiency
- Capacity-constrained scheduling
- Interdependency awareness

✅ **Multi-Equipment Fleet Management**
- Fleet-wide health aggregation
- Prioritized maintenance queue
- Batch maintenance opportunities
- 30-day maintenance planning

✅ **What-If Analysis**
- Impact of delay scenarios
- Failure probability projection
- Production loss estimation
- Recommendation generation

## Integration with Existing System

The new dynamic system **maintains backward compatibility**:
- Existing API endpoints still work
- `compute_health_index()` in `rul_predictor.py` unchanged
- New `v2` endpoints provide advanced features
- Legacy code not affected

### Migration Path

1. **Phase 1** (Now): Add new v2 endpoints, use dynamic calculation
2. **Phase 2**: Update UI to use new detailed metrics
3. **Phase 3**: Deprecate v1 endpoints, move to v2 only

## Performance Considerations

- **Caching**: History is cached per equipment per window
- **Async Support**: All heavy computations can run async
- **Scalability**: Designed for 100+ equipment without degradation
- **Real-time**: Updates every 60 seconds in proactive monitor

## Future Enhancements

🔮 **Planned Features**:
- ML-based failure prediction (XGBoost integration)
- Spare parts optimization (predict need, order timing)
- Technician skill matching (assign right person to job)
- Weather-based maintenance scheduling
- Production schedule integration
- Multi-site fleet optimization
- Predictive spare parts ordering
- Equipment lifecycle cost analysis

---

**System Version**: 2.0.0  
**Last Updated**: 2026-06-14  
**Status**: Production Ready ✅
