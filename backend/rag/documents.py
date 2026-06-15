"""
Synthetic Tata Steel industrial knowledge base.
Covers: SOPs, failure analysis reports, maintenance logs, and best practices
for blast furnace pumps, conveyors, cooling systems, and rolling mills.
"""

KNOWLEDGE_DOCUMENTS = [
    {
        "id": "SOP-PUMP-001",
        "title": "SOP: Centrifugal Pump Bearing Maintenance – Blast Furnace Cooling Circuit",
        "content": """
STANDARD OPERATING PROCEDURE – PUMP BEARING MAINTENANCE
Document ID: SOP-PUMP-001 | Rev: 4.2 | Effective: 2024-01-15
Applicable Equipment: BF-Pump-10 through BF-Pump-14 (Jamshedpur Plant)

1. PURPOSE
This SOP defines the preventive and corrective maintenance procedures for centrifugal
pump bearings used in the blast furnace cooling water circuit.

2. NORMAL OPERATING PARAMETERS
- Bearing Temperature: 50°C – 80°C (alarm at 85°C, shutdown at 95°C)
- Vibration Velocity: 0.1 – 0.5 mm/s RMS (alarm at 0.7 mm/s, shutdown at 1.0 mm/s)
- Discharge Pressure: 90 – 110 PSI (alarm below 80 PSI or above 120 PSI)
- Lubricant Oil Temperature: 45°C – 65°C
- Motor Current Draw: 85% – 105% of nameplate FLA

3. FAULT INDICATORS AND RESPONSE
Overheating (Bearing Temp > 85°C):
  - Primary cause: Lubrication failure (blocked supply line, depleted grease, contaminated oil)
  - Secondary cause: Excessive radial/axial load, misalignment, bearing wear
  - Immediate action: Verify oil level and flow, check lubrication pump pressure
  - Corrective action: Replace lubrication line filter, flush and refill oil reservoir

High Vibration (> 0.7 mm/s):
  - Primary cause: Bearing race wear, cavitation, rotor imbalance
  - Secondary cause: Coupling misalignment, foundation looseness
  - Immediate action: Reduce pump speed by 10%, check coupling alignment
  - Corrective action: Balance rotor, replace bearing, re-align coupling

Low Discharge Pressure (< 80 PSI):
  - Primary cause: Impeller wear, cavitation, suction line blockage
  - Secondary cause: Worn wear rings, excessive clearance
  - Immediate action: Check suction strainer, verify NPSH conditions
  - Corrective action: Replace impeller and wear rings

4. LUBRICATION SCHEDULE
- Grease re-lubrication: Every 2,000 operating hours or 3 months
- Oil change (circulating oil system): Every 4,000 hours or 6 months
- Vibration trending: Weekly via portable analyzer
- Infrared thermography: Monthly on all bearing housings
- Oil analysis (viscosity, contamination): Quarterly

5. BEARING REPLACEMENT CRITERIA
Replace bearing when:
- Vibration exceeds 0.7 mm/s for more than 48 continuous hours
- Temperature exceeds 85°C after lubrication correction
- Oil analysis shows metal particle count > 150 ppm
- Bearing noise changes to grinding or irregular rumbling
- RUL prediction model indicates < 7 days remaining

6. SPARE PARTS LIST
- SKF 6315-2RS1/C3 Deep Groove Ball Bearing (Drive End)
- SKF NJ 315 ECP Cylindrical Roller Bearing (Non-Drive End)
- Castrol Tribol 800/1 Grease (400g cartridge)
- Shell Tellus S2 VX 46 Hydraulic/Lubrication Oil (20L)
""",
        "category": "SOP",
        "equipment_type": "pump",
        "fault_types": ["overheating", "vibration", "lubrication_failure", "bearing_failure"]
    },
    {
        "id": "SOP-LUBRICATION-001",
        "title": "SOP: Industrial Lubrication System Inspection and Maintenance",
        "content": """
STANDARD OPERATING PROCEDURE – LUBRICATION SYSTEM INSPECTION
Document ID: SOP-LUBRICATION-001 | Rev: 2.8 | Effective: 2024-03-01
Applicable Equipment: All rotating machinery, Jamshedpur & Kalinganagar Plants

1. PURPOSE
Ensure continuous and adequate lubrication to all critical rotating equipment to prevent
premature bearing failure, reduce unplanned downtime, and extend component life.

2. LUBRICATION FAILURE MODES
2.1 Blocked Supply Line
- Symptoms: Rising bearing temperature, reduced oil flow indicator alarm
- Root cause: Debris accumulation in inline filter, sludge buildup in supply line
- Detection: Oil pressure differential across filter > 0.8 bar
- Action: Replace filter element, flush supply line with clean solvent

2.2 Oil Degradation
- Symptoms: Discolored oil (dark brown/black), burnt smell, increased viscosity
- Root cause: Oxidation from excessive temperature, water contamination, metallic wear particles
- Detection: Oil analysis viscosity > 20% deviation from baseline
- Action: Immediate oil drain and refill, investigate root contamination source

2.3 Seal Failure
- Symptoms: Oil leakage at bearing housing, low oil level in reservoir
- Root cause: Worn lip seals, excessive shaft runout causing seal damage
- Detection: Visual inspection at weekly walkdown, oil level trending
- Action: Replace lip seals, check shaft runout (max 0.05mm TIR)

2.4 Pump Failure (Lubrication Circuit Pump)
- Symptoms: Zero or low oil flow, pressure below set point
- Root cause: Worn pump vanes/gears, motor failure, cavitation
- Detection: Oil pressure transducer reading < 1.5 bar (set point 2.5 bar)
- Action: Switch to backup lubrication pump immediately, overhaul primary pump

3. PREDICTIVE INDICATORS
Oil Temperature Increase Rate:
- Normal: < 0.5°C/hour during steady operation
- Warning: 0.5 – 2.0°C/hour (investigate within 4 hours)
- Critical: > 2.0°C/hour (immediate action required)

Vibration Correlation:
- Lubrication deficiency typically increases vibration by 15-40% before temperature rise
- Monitor vibration trend as leading indicator for lubrication issues
""",
        "category": "SOP",
        "equipment_type": "lubrication_system",
        "fault_types": ["lubrication_failure", "oil_degradation", "seal_failure"]
    },
    {
        "id": "FAILURE-RPT-2024-047",
        "title": "Failure Analysis Report: Catastrophic Bearing Failure – BF-Pump-09",
        "content": """
FAILURE ANALYSIS REPORT
Report ID: FAR-2024-047 | Date: 2024-08-14 | Plant: Jamshedpur
Equipment: BF-Pump-09 (Blast Furnace #3 Cooling Water Pump)
Failure Type: Catastrophic Bearing Failure | RCA Method: Fishbone + FTA

EXECUTIVE SUMMARY
BF-Pump-09 suffered a catastrophic drive-end bearing failure on 2024-08-14 at 03:42,
causing 18 hours of unplanned downtime and $82,000 in direct losses.
Root cause was identified as progressive lubrication starvation over 14 days.

TIMELINE OF EVENTS
2024-07-31: Vibration increased from 0.31 to 0.45 mm/s (unnoticed, below alarm)
2024-08-03: Oil temperature in reservoir rose from 52°C to 61°C
2024-08-07: Bearing temperature first exceeded 80°C (acknowledged, action deferred)
2024-08-10: Inline filter differential pressure alarm triggered (not investigated promptly)
2024-08-12: Bearing temperature reached 88°C; maintenance ticket raised as P2 (should be P1)
2024-08-14 03:42: Bearing temperature spiked to 104°C in <10 minutes; catastrophic failure

ROOT CAUSE ANALYSIS
Primary Root Cause: Blocked lubrication supply line filter (debris from corroded pipe section)
Contributing Factor 1: Inline filter differential pressure alarm response SLA of 8 hours – too slow
Contributing Factor 2: Vibration trending not reviewed weekly as per SOP-PUMP-001
Contributing Factor 3: RUL prediction model not in use at time of failure

CORRECTIVE ACTIONS IMPLEMENTED
1. Replaced all inline lubrication filters plant-wide (immediate)
2. Replaced corroded suction pipe section (48-hour action)
3. Implemented automated differential pressure monitoring with 2-hour alarm response SLA
4. Deployed AI predictive maintenance system for all 14 blast furnace pumps
5. Weekly vibration trending review added to operator checklist

LESSONS LEARNED
- Multi-sensor correlation (vibration rise + oil temperature + differential pressure)
  provides 7-14 days of advance warning before catastrophic failure
- P1 escalation threshold changed: bearing temp > 85°C with any secondary indicator → immediate P1
- Lubrication system health is a leading indicator, not a lagging one

FINANCIAL IMPACT
Direct losses: $82,000 (bearing, labour, emergency parts)
Production loss: $340,000 (18 hours × blast furnace production rate)
Total: $422,000 — preventable with predictive maintenance
""",
        "category": "FAILURE_REPORT",
        "equipment_type": "pump",
        "fault_types": ["bearing_failure", "lubrication_failure", "overheating"]
    },
    {
        "id": "MAINT-LOG-2024-Q3",
        "title": "Maintenance History Log: Q3 2024 – Rotating Equipment",
        "content": """
MAINTENANCE HISTORY LOG – Q3 2024
Plant: Jamshedpur | Period: July – September 2024
Equipment Category: Rotating Equipment (Pumps, Fans, Compressors)

PUMP MAINTENANCE EVENTS
2024-07-04 | BF-Pump-11 | Routine: Grease relubrication (2,000-hour interval)
  Technician: S. Mishra | Duration: 45 min | Findings: Normal wear, grease contaminated with rust particles
  Action: Added inline magnetic separator to lube supply line

2024-07-18 | BF-Pump-12 | Corrective: Vibration reduction (0.68 mm/s peak observed)
  Technician: R. Sharma | Duration: 6 hours | Findings: Coupling misalignment (0.12mm offset)
  Action: Realigned coupling to within 0.02mm, baseline vibration now 0.28 mm/s

2024-08-02 | Cooling-Fan-3 | Predictive: Temperature trend increasing (75°C vs baseline 62°C)
  Technician: A. Kumar | Duration: 4 hours | Findings: Drive belt slipping, tension 15% below spec
  Action: Replaced drive belt, adjusted tension, reset temperature baseline

2024-08-14 | BF-Pump-09 | EMERGENCY: Catastrophic bearing failure (see FAR-2024-047)
  Duration: 18 hours | Total cost: $422,000

2024-08-22 | BF-Pump-09 | Corrective: Full pump overhaul post-failure
  Technician: M. Patel, vendor: SKF Services | Duration: 72 hours
  Action: Replaced both bearings, renewed seals, replaced lubrication supply piping

2024-09-05 | Conveyor-B | Predictive: Vibration asymmetry detected (0.52 mm/s left vs 0.28 mm/s right)
  Technician: R. Sharma | Duration: 3 hours | Findings: Belt tracker misaligned, idler bearing wear
  Action: Replaced 3 idler bearings, realigned belt tracker

2024-09-19 | BF-Pump-12 | Corrective: Impeller wear replacement
  Technician: M. Patel | Duration: 8 hours | Findings: 2.3mm clearance (limit 1.5mm)
  Action: Replaced impeller and wear rings, restored pressure to 105 PSI

RELIABILITY KPIs Q3 2024
Total Unplanned Downtime: 24.8 hours (target: <15 hours)
Predictive Maintenance Interventions: 8 (prevented estimated 142 hours downtime)
Mean Time Between Failures (MTBF): 2,840 hours (target: 3,000 hours)
Maintenance Cost per Unit Output: 14.2 USD/ton (target: 12 USD/ton)
""",
        "category": "MAINTENANCE_LOG",
        "equipment_type": "rotating_equipment",
        "fault_types": ["vibration", "overheating", "bearing_failure", "belt_wear"]
    },
    {
        "id": "SOP-VIBRATION-001",
        "title": "SOP: Vibration Analysis and Condition Monitoring – Steel Plant Equipment",
        "content": """
STANDARD OPERATING PROCEDURE – VIBRATION ANALYSIS
Document ID: SOP-VIBRATION-001 | Rev: 3.1 | Effective: 2024-02-01
Standard: ISO 10816-3 (Industrial Machines 15-300 kW)

1. VIBRATION SEVERITY CLASSIFICATIONS (ISO 10816-3)
Zone A: < 0.28 mm/s — New equipment, acceptable for continuous operation
Zone B: 0.28 – 0.71 mm/s — Acceptable for long-term operation
Zone C: 0.71 – 1.8 mm/s — Unsatisfactory for long-term operation; corrective action within 30 days
Zone D: > 1.8 mm/s — Sufficiently severe to cause equipment damage; immediate shutdown

2. VIBRATION FAULT SIGNATURES
Imbalance:
- 1× RPM dominant frequency
- Present in radial direction (horizontal and vertical)
- Common cause: Corrosion/material buildup on rotor, operating at critical speed

Misalignment:
- 1× and 2× RPM dominant (angular misalignment)
- 2× RPM dominant (parallel misalignment)
- Present in axial direction predominantly

Bearing Defects:
- BPFI, BPFO, BSF, FTF frequencies (bearing defect frequencies)
- High-frequency broadband energy (>1000 Hz in acceleration spectrum)
- Sub-harmonics of running speed
- Early detection: Spike energy (gSE) or kurtosis > 10

Resonance:
- Large amplitude at specific RPM (critical speed)
- Phase shift of 90° at resonance
- Amplified by imbalance, misalignment, or looseness

3. ALARM SETPOINTS FOR BLAST FURNACE PUMPS
Overall Vibration (velocity, 10-1000 Hz): Alert 0.50 mm/s, Alarm 0.70 mm/s, Trip 1.0 mm/s
Bearing Housing Temperature: Alert 80°C, Alarm 85°C, Trip 95°C
Spike Energy (gSE): Alert 5, Alarm 10, Trip 15

4. TRENDING AND RUL CORRELATION
Vibration degradation rate > 0.02 mm/s per week: Estimated RUL < 60 days
Vibration degradation rate > 0.05 mm/s per week: Estimated RUL < 30 days
Vibration degradation rate > 0.10 mm/s per week: Estimated RUL < 14 days
Temperature degradation rate > 1°C/day (sustained): Estimated RUL < 21 days
Combined (vibration + temperature trending up): Apply conservative (lower) RUL estimate
""",
        "category": "SOP",
        "equipment_type": "rotating_equipment",
        "fault_types": ["vibration", "imbalance", "misalignment", "bearing_defect"]
    },
    {
        "id": "SOP-RUL-GUIDE-001",
        "title": "Predictive Maintenance Guide: RUL Estimation and Maintenance Scheduling",
        "content": """
PREDICTIVE MAINTENANCE TECHNICAL GUIDE – RUL ESTIMATION
Document ID: PM-GUIDE-001 | Rev: 1.5 | Effective: 2024-06-01
Applicable to: All critical rotating equipment, Tata Steel Plants

1. HEALTH INDEX CALCULATION
Health Index (HI) is a normalized score 0-100:
  HI = 100 × w1 × (1 - T_dev/T_max) + w2 × (1 - V_level/V_max) + w3 × (1 - P_dev/P_max)
Where:
  T_dev = |current_temp - nominal_temp| / nominal_temp
  V_level = current_vibration / max_vibration
  P_dev = |current_pressure - nominal_pressure| / nominal_pressure
  w1=0.40, w2=0.35, w3=0.25 (vibration is leading indicator)

Interpretation:
  HI > 85: Healthy – No action required
  HI 70-85: Good – Monitor closely, schedule routine maintenance
  HI 50-70: Degraded – Plan maintenance within 30 days
  HI 30-50: Poor – Schedule maintenance within 7 days
  HI < 30: Critical – Immediate maintenance required, consider shutdown

2. RUL ESTIMATION FORMULA
RUL (days) = HI × degradation_factor / daily_degradation_rate
Where:
  daily_degradation_rate = estimated from recent sensor trend (past 7 days)
  degradation_factor = 0.5 for pumps, 0.7 for conveyors, 0.4 for fans

For temperature-dominant degradation (T > 85°C):
  RUL = (T_shutdown - T_current) / daily_temperature_rise_rate

For vibration-dominant degradation (V > 0.5 mm/s):
  RUL = (V_trip - V_current) / daily_vibration_rise_rate

3. MAINTENANCE SCHEDULING PRIORITIES
P1 (Immediate – within 24 hours): HI < 30 OR Failure Probability > 80% OR RUL < 5 days
P2 (Urgent – within 72 hours): HI 30-50 OR Failure Probability 50-80% OR RUL 5-14 days
P3 (Planned – within 30 days): HI 50-70 OR Failure Probability 20-50% OR RUL 14-45 days
Routine: HI > 70 AND Failure Probability < 20% AND RUL > 45 days

4. WHAT-IF DELAY ANALYSIS
When maintenance is delayed, account for accelerated degradation:
  New_failure_prob = 1 - (1 - current_failure_prob) × exp(-delay_days / RUL)
  Additional_financial_risk = delay_days × daily_production_loss × new_failure_prob

For Blast Furnace Pumps:
  Production loss if pump fails: $45,000/hour
  Planned maintenance cost: $4,500
  Emergency repair cost: $22,000 (5× planned)
  Break-even delay threshold: typically 2-4 days for critical pumps
""",
        "category": "TECHNICAL_GUIDE",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "EMERGENCY-PROC-001",
        "title": "Emergency Response Procedure: Critical Equipment Failure – Steel Plant",
        "content": """
EMERGENCY RESPONSE PROCEDURE – CRITICAL EQUIPMENT FAILURE
Document ID: ERP-001 | Rev: 2.3 | Effective: 2024-01-01
Trigger: Any equipment reaching CRITICAL or EMERGENCY risk level

1. IMMEDIATE RESPONSE (0-15 minutes)
Step 1: Alert shift supervisor via P.A. and emergency contact list
Step 2: If bearing temp > 95°C or vibration > 1.0 mm/s: initiate controlled shutdown
Step 3: Switch to backup equipment (where available)
Step 4: Isolate energy sources (LOTO – Lockout/Tagout per safety SOP)
Step 5: Notify maintenance team lead

2. RAPID ASSESSMENT (15-60 minutes)
Step 6: Visual inspection of failed/failing component
Step 7: Oil sample collection for analysis
Step 8: Vibration spot-check on adjacent machines
Step 9: Estimate repair time and production impact

3. COMMUNICATION PROTOCOL
Notify within 1 hour: Plant Manager, Maintenance Manager, Production Manager
Notify within 4 hours: Division Head, if downtime exceeds 4 hours
Document: All actions in Maintenance Management System (SAP PM module)

4. ROOT CAUSE INVESTIGATION
Must be completed within 72 hours for any unplanned downtime > 4 hours.
Use 5-Why methodology and Fishbone (Ishikawa) diagram.
Report format: FAR (Failure Analysis Report) – see template FAR-TEMPLATE-001

5. RESTART PROCEDURE
All clear must be confirmed by:
- Maintenance lead (mechanical integrity)
- Electrical safety officer (motor and controls)
- Shift supervisor (process readiness)
Commissioning vibration check: must be < 0.3 mm/s before returning to normal operation
""",
        "category": "EMERGENCY_PROCEDURE",
        "equipment_type": "all",
        "fault_types": ["bearing_failure", "overheating", "catastrophic_failure"]
    },
    {
        "id": "CONVEYOR-MAINT-001",
        "title": "SOP: Belt Conveyor Maintenance and Inspection – Raw Material Handling",
        "content": """
STANDARD OPERATING PROCEDURE – BELT CONVEYOR MAINTENANCE
Document ID: SOP-CONVEYOR-001 | Rev: 2.1 | Effective: 2024-04-15
Applicable Equipment: Conveyor-A through Conveyor-F, Iron Ore Handling System

1. NORMAL OPERATING PARAMETERS
- Belt speed: 2.0 – 3.5 m/s
- Belt tension: 45 – 65 kN (alarm at 40 kN low, 70 kN high)
- Idler bearing temperature: < 60°C (alarm at 65°C)
- Drive pulley vibration: < 0.4 mm/s
- Motor current draw: 85-105% of nameplate

2. INSPECTION SCHEDULE
Daily (operator walkdown):
- Visual check for belt tears, edge damage, material spillage
- Check belt tracking (should be centered, ±25mm maximum)
- Verify emergency pull cord functionality

Weekly (maintenance check):
- Measure belt tension at head and tail pulleys
- Vibration spot-check on all drive components
- Lubricate idler bearings (high-dust environment: every 250 hours)
- Inspect belt splices for separation

Monthly:
- Full belt inspection (upper and lower surfaces)
- Replace any idlers showing vibration > 0.4 mm/s or temperature > 60°C
- Belt alignment check across full length

3. BELT TEAR DETECTION AND RESPONSE
Belt tear indicators:
- Acoustic sensors detect change in impact frequency
- Vibration asymmetry between left/right sides > 50%
- Material flow sensor detects bypass (material falling through)

Response to belt tear:
- Immediate: Reduce speed to 1.0 m/s, alert supervisor
- If tear length > 100mm: Stop conveyor, apply temporary clamp
- If tear at splice: Emergency splice repair (< 4 hours)
- Root cause: Foreign object, overloading, belt aging (>3 years), misalignment

4. ESTIMATED REPAIR TIMES
Minor belt repair (< 0.5m tear): 2 hours
Belt splice repair: 4 hours
Idler replacement (single): 30 minutes
Idler replacement (multiple per section): 2-4 hours
Full belt replacement: 24-48 hours
""",
        "category": "SOP",
        "equipment_type": "conveyor",
        "fault_types": ["belt_tear", "idler_failure", "misalignment", "vibration"]
    },
    {
        "id": "SPARE-PARTS-001",
        "title": "Spare Parts Catalog and Procurement Lead Times – Critical Equipment",
        "content": """
TATA STEEL JAMSHEDPUR – CRITICAL SPARE PARTS CATALOG
Document ID: SPARE-PARTS-001 | Rev: 3.0 | Updated: 2024-10-01
Central Stores: Building 14, Jamshedpur Main Plant

=== PUMP SPARE PARTS (BF-Pump-10 to BF-Pump-14) ===

1. BEARINGS
   Part: SKF 6315-2RS1/C3 (Drive End Bearing)
   Stock: 6 units | Min Reorder: 4 | Reorder Level: 2
   Lead Time: 3 days (domestic supplier, Tata Bearing Ltd)
   Emergency: Same-day from Kolkata distributor (premium cost)
   Unit Cost: Rs 4,200 | Shelf Life: 5 years

   Part: SKF 6215-2RS1 (Non-Drive End Bearing)
   Stock: 8 units | Min Reorder: 4
   Lead Time: 3 days (domestic)
   Unit Cost: Rs 2,800

   Part: SKF 22320 EK/C3 (Spherical Roller Bearing, heavy pumps)
   Stock: 2 units (CRITICAL LOW)
   Lead Time: 14 days (import from Sweden) | Emergency: 7 days airfreight
   Unit Cost: Rs 18,500
   ALERT: Reorder immediately if stock falls below 2

2. MECHANICAL SEALS
   Part: John Crane 8B1 Mechanical Seal Set (65mm shaft)
   Stock: 3 sets | Min Reorder: 2
   Lead Time: 7 days (Chennai distributor)
   Unit Cost: Rs 18,500
   Note: Must be replaced with bearing if seal leakage detected

   Part: Flowserve CWSE Seal (for high-pressure pumps)
   Stock: 1 set (LOW STOCK)
   Lead Time: 21 days (import USA)
   Unit Cost: Rs 45,000

3. IMPELLERS
   Part: Cast Iron Impeller 250mm (standard BF pumps)
   Stock: 1 unit (CRITICAL – order immediately)
   Lead Time: 21 days (OEM Kirloskar, Pune)
   Emergency: 10 days (premium OEM channel)
   Unit Cost: Rs 85,000
   Note: Single-source supplier – maintain minimum 2 units

4. LUBRICATION SYSTEM
   Part: Shell Tellus S2 VX 46 Hydraulic/Lube Oil (20L drum)
   Stock: 12 drums | Consumption: ~2 drums/month/pump
   Lead Time: 1 day (local distributor)
   Unit Cost: Rs 4,800/drum

   Part: Lubrication Filter Element LF-2024 (Inline, 25 micron)
   Stock: 15 units | Replacement interval: Every 2000 hours
   Lead Time: 2 days
   Unit Cost: Rs 850

   Part: Oil Temperature Sensor PT100 (4-20mA, -50 to 200°C)
   Stock: 4 units
   Lead Time: 5 days
   Unit Cost: Rs 3,200

5. GASKETS AND SEALS
   Part: Pump Casing Gasket Set (BF-10 to 14 compatible)
   Stock: 10 sets
   Lead Time: 2 days
   Unit Cost: Rs 1,200

=== CONVEYOR SPARE PARTS ===

6. Part: Belt Splice Kit EP500/3 (1400mm belt width)
   Stock: 3 kits | Emergency consumption: 1 per splice
   Lead Time: 5 days | Emergency: 2 days (Chennai)
   Unit Cost: Rs 28,000

7. Part: Conveyor Idler Set – Impact Zone (5-roll set, 150mm diameter)
   Stock: 20 sets
   Lead Time: 1 day (local)
   Unit Cost: Rs 1,200/set

8. Part: Drive Pulley Lagging Sheet (10mm rubber, 1400mm width)
   Stock: 4 sheets
   Lead Time: 7 days
   Unit Cost: Rs 8,500/sheet

=== COOLING FAN SPARE PARTS ===

9. Part: Fan Blade Assembly (1200mm, 6-blade, aluminum)
   Stock: 2 sets
   Lead Time: 14 days (OEM)
   Unit Cost: Rs 32,000

10. Part: Fan Shaft Bearing Set (SKF 6312-2RS1)
    Stock: 6 units
    Lead Time: 2 days
    Unit Cost: Rs 1,800

=== PROCUREMENT PROCESS ===

EMERGENCY PROCUREMENT (P1 – same day):
- Phone approval from Plant Manager
- Dispatch from Central Stores within 2 hours
- For out-of-stock: emergency purchase from approved vendor list
- Budget: Up to Rs 1,00,000 without committee approval

URGENT PROCUREMENT (P2 – 24-hour cycle):
- SAP PM requisition raised by maintenance supervisor
- Stores approval within 4 hours
- Vendor dispatch: next business day

PLANNED PROCUREMENT (P3 – weekly cycle):
- Weekly PM planning meeting (Tuesdays)
- Standard purchase order, 3-5 day lead time
- Bulk discounts applied for quarterly orders

CRITICAL STOCK ALERTS (as of 2024-10-01):
- SKF 22320 EK/C3 bearing: Stock=2 (REORDER NOW – 14d lead time)
- Cast Iron Impeller 250mm: Stock=1 (REORDER NOW – 21d lead time)
- Flowserve CWSE Seal: Stock=1 (REORDER NOW – 21d lead time)

APPROVED VENDORS:
- Bearings: Tata Bearing Ltd, SKF India, NRB Bearings
- Seals: John Crane India, Flowserve India, Burgmann
- Lubricants: Shell India, Castrol Industrial
- Impellers: Kirloskar Brothers, Grundfos India
""",
        "category": "procurement",
        "equipment_type": "all",
        "fault_types": ["spare_parts", "procurement", "inventory", "lead_time", "bearing", "seal", "impeller"]
    },
    {
        "id": "SOP-FAN-001",
        "title": "SOP: Cooling Fan and Motor Bearing Maintenance – Sinter Plant",
        "content": """
STANDARD OPERATING PROCEDURE – COOLING FAN MAINTENANCE
Document ID: SOP-FAN-001 | Rev: 1.9 | Effective: 2024-05-01
Applicable Equipment: Cooling-Fan-1 through Cooling-Fan-6, Sinter Plant Jamshedpur

1. NORMAL OPERATING PARAMETERS
- Fan Bearing Temperature: 40°C – 65°C (alarm at 70°C, shutdown at 80°C)
- Vibration Velocity (overall): < 0.35 mm/s RMS (alarm at 0.45 mm/s, shutdown at 0.60 mm/s)
- Drive Belt Tension: 40–55 kN (alarm below 35 kN)
- Motor Current: 85–105% nameplate FLA
- Airflow (design): 18,000 – 22,000 m³/hour
- Blade tip clearance: 15 – 25mm (alarm if > 30mm or < 10mm)

2. FAULT INDICATORS AND RESPONSE
Fan Bearing Overheating (Temp > 70°C):
  - Primary cause: Insufficient grease, high-ambient-temperature operation, misaligned shaft
  - Secondary cause: Drive belt slip causing bearing to run hot due to harmonic excitation
  - Immediate action: Check grease nipple, apply 5g of Castrol Tribol 3020/1000-1 grease
  - Corrective action: Realign shaft, replace bearing if temperature exceeds 75°C after greasing

Belt Drive Issues:
  - Slipping belt: Motor current drops while fan speed decreases; check sheave condition
  - Cracked belt: Vibration asymmetry between drive and non-drive ends increases > 30%
  - Corrective action: Replace V-belt set (all belts simultaneously), re-tension to spec

Blade Fouling (Steel Dust Accumulation):
  - Symptoms: Vibration increase 1×RPM, airflow reduction > 10%
  - Corrective action: Shut down, lock out, clean blades with compressed air + wire brush

3. LUBRICATION SCHEDULE
- Grease re-lubrication (high-dust environment): Every 500 operating hours
- Bearing replacement criterion: Vibration > 0.45 mm/s sustained 24 hours
- Belt inspection: Weekly; replacement interval 6 months or 8,000 hours

4. SPARE PARTS
- SKF 6312-2RS1/C3 Ball Bearing: Stock minimum 4 units
- Gates PowerBand V-Belt B78 (set of 3): Stock minimum 2 sets
- Fan Blade (aluminum, 1200mm, 6-blade): Stock minimum 1 set
""",
        "category": "SOP",
        "equipment_type": "fan",
        "fault_types": ["overheating", "vibration", "belt_wear", "blade_fouling"]
    },
    {
        "id": "SOP-IMPELLER-001",
        "title": "SOP: Centrifugal Pump Impeller Inspection and Replacement",
        "content": """
STANDARD OPERATING PROCEDURE – PUMP IMPELLER INSPECTION
Document ID: SOP-IMPELLER-001 | Rev: 2.3 | Effective: 2024-07-01
Applicable Equipment: All centrifugal pumps BF-Pump-10 to BF-Pump-14

1. IMPELLER WEAR INDICATORS
Discharge pressure drop (< 85 PSI sustained):
  - Normal new impeller clearance: 0.3 – 0.5mm
  - Warning: clearance > 1.0mm (pressure drop ~12%)
  - Critical: clearance > 1.5mm (pressure drop > 20%, replace immediately)
  - Annual measurement required: use feeler gauge at wear ring

Cavitation Damage:
  - Visual: Pitting/erosion on inlet vane faces (honeycomb appearance)
  - Acoustic: High-frequency cracking/rattling during operation
  - Vibration: Broadband vibration increase without clear frequency peak
  - Cause: Operating below minimum NPSH (net positive suction head)

Hydraulic Imbalance:
  - Vibration 1×RPM, increasing with pump speed
  - Caused by uneven wear between vanes or material buildup on one side

2. REPLACEMENT PROCEDURE
Step 1: Isolate pump (LOTO procedure per ERP-001)
Step 2: Drain pump casing; collect fluid sample for analysis
Step 3: Remove coupling, bearing housing, and mechanical seal
Step 4: Measure current clearance (feeler gauge between impeller and wear ring)
Step 5: If clearance > 1.5mm → replace impeller and wear rings as a set
Step 6: Inspect casing for erosion (replace if wall thickness < 8mm)
Step 7: Install new impeller; torque to 95 Nm; verify dynamic balance (target < 0.8 g-mm)
Step 8: Re-assemble; commission vibration check (must be < 0.30 mm/s before handover)

3. POST-REPLACEMENT COMMISSIONING
- Verify discharge pressure returns to > 95 PSI within 15 minutes at design flow
- Take baseline vibration signature and archive in SAP PM
- Log impeller serial number and clearance measurement in maintenance record
""",
        "category": "SOP",
        "equipment_type": "pump",
        "fault_types": ["impeller_wear", "cavitation", "low_pressure", "vibration"]
    },
    {
        "id": "FAR-2024-089",
        "title": "Failure Analysis Report: Conveyor Drive Bearing Progressive Failure – Conveyor-C",
        "content": """
FAILURE ANALYSIS REPORT
Report ID: FAR-2024-089 | Date: 2024-10-22 | Plant: Jamshedpur
Equipment: Conveyor-C (Iron Ore Handling, Raw Material Yard)
Failure Type: Progressive Drive Bearing Failure | RCA Method: 5-Why + Vibration Signature Analysis

EXECUTIVE SUMMARY
Conveyor-C suffered a drive-end bearing failure on 2024-10-22 causing 11 hours of unplanned downtime.
Root cause: Accelerated bearing wear due to belt misalignment and inadequate lubrication interval in
high-dust environment. Total financial impact: ₹98 Lakhs (production loss + emergency repair).

TIMELINE OF EVENTS
2024-10-01: Routine inspection noted belt tracking deviation of 38mm (limit: 25mm). Not corrected.
2024-10-08: Vibration asymmetry left/right increased from 12% to 31% (threshold 50%, not alarmed)
2024-10-12: Idler bearing temperature at position C-07 reached 63°C (alarm at 65°C)
2024-10-18: Drive bearing vibration reached 0.38 mm/s (ZONE B, per SOP-VIBRATION-001)
2024-10-20: Operator noted unusual noise from drive head. Maintenance deferred to weekend.
2024-10-22 14:17: Drive bearing catastrophic failure. Belt stopped. Plant production halted.

ROOT CAUSE ANALYSIS (5-WHY)
Why 1: Drive bearing failed — Excessive radial load due to belt misalignment
Why 2: Belt misalignment not corrected — inspection finding not escalated to P2 work order
Why 3: Vibration asymmetry not alarmed — alarm threshold set for overall vibration, not asymmetry
Why 4: Lubrication interval not shortened for dust environment — SOP-CONVEYOR-001 §3 not applied
Why 5: Predictive maintenance system not monitoring conveyor drive end bearing temperature trend

CORRECTIVE ACTIONS
1. Belt realigned to ±15mm tolerance (immediate)
2. Drive-end bearing replaced (SKF 22220 EK/C3, 48-hour action)
3. Lubrication interval shortened: 250 hours → 125 hours for drive-end in high-dust zones
4. Vibration asymmetry alarm configured: >40% left/right differential triggers P2 alert
5. AI predictive system extended to all 6 conveyors (drive-end temperature + vibration trending)
6. Weekly belt tracking check added to operator checklist

LESSONS LEARNED
- In high-dust environments, lubrication intervals must be halved from standard schedule
- Belt misalignment > 30mm is a leading indicator for accelerated bearing wear (lead time: 2-3 weeks)
- Asymmetric vibration monitoring is more sensitive than overall vibration for conveyor drive failures

FINANCIAL IMPACT
Production loss: ₹84 Lakhs (11 hours × iron ore handling rate)
Emergency repair: ₹14 Lakhs (bearing, seal, emergency vendor)
Total: ₹98 Lakhs — preventable with P2 work order at first inspection finding
""",
        "category": "FAILURE_REPORT",
        "equipment_type": "conveyor",
        "fault_types": ["bearing_failure", "belt_misalignment", "vibration", "lubrication_failure"]
    },
    {
        "id": "SOP-ALIGNMENT-001",
        "title": "SOP: Laser Shaft Alignment and Dynamic Balancing – Rotating Equipment",
        "content": """
STANDARD OPERATING PROCEDURE – SHAFT ALIGNMENT AND BALANCING
Document ID: SOP-ALIGNMENT-001 | Rev: 3.0 | Effective: 2024-03-15
Applicable Equipment: All coupled rotating equipment, Jamshedpur Plant

1. WHEN ALIGNMENT IS REQUIRED
Mandatory realignment after:
  - Any bearing replacement
  - Coupling replacement
  - Base plate modification or grouting repair
  - Vibration increase > 0.15 mm/s from baseline (suspected misalignment)
  - After any thermal expansion event (cool-down and restart cycle)

2. ALIGNMENT TOLERANCES (LASER METHOD)
Pump-Motor Couplings (up to 1500 RPM):
  - Parallel offset: ≤ 0.05 mm (acceptable), ≤ 0.02 mm (excellent)
  - Angular: ≤ 0.05 mm/100mm (acceptable), ≤ 0.02 mm/100mm (excellent)

High-speed equipment (> 1500 RPM):
  - Parallel offset: ≤ 0.02 mm
  - Angular: ≤ 0.02 mm/100mm

3. ALIGNMENT PROCEDURE
Step 1: Install laser alignment system (Fluke 830 or equivalent)
Step 2: Rotate shaft slowly; take 3 readings at 0°, 90°, 180°, 270°
Step 3: Calculate offset and angular values; compare to tolerance
Step 4: Adjust shims under motor feet (start with rear feet)
Step 5: Final verification: rotate shaft 360°, confirm repeatability ±0.01mm
Step 6: Torque all foundation bolts to specification; repeat verification

4. VIBRATION ACCEPTANCE AFTER ALIGNMENT
Post-alignment commissioning check:
  - Run at design speed for 30 minutes
  - Overall vibration must be < 0.30 mm/s RMS
  - 1× and 2× RPM amplitudes must drop by ≥ 40% compared to pre-alignment baseline
  - Record and archive baseline spectrum in SAP PM for future trending

5. THERMAL GROWTH COMPENSATION
For hot-service pumps (operating temp > 80°C):
  - Cold alignment offset: +0.15mm vertical (motor higher) for pump thermal growth
  - Verify hot alignment after 4 hours at operating temperature using proximity probes
""",
        "category": "SOP",
        "equipment_type": "rotating_equipment",
        "fault_types": ["misalignment", "vibration", "bearing_failure"]
    },
    {
        "id": "INSPECTION-IR-001",
        "title": "Infrared Thermography Inspection Procedure – Rotating Equipment and Electrical",
        "content": """
INFRARED THERMOGRAPHY INSPECTION PROCEDURE
Document ID: INSPECTION-IR-001 | Rev: 2.1 | Effective: 2024-01-20
Standard: ISO 18434-1 | Equipment: FLIR T840 / T1020 Thermal Camera

1. INSPECTION INTERVALS
Critical rotating equipment (BF pumps, conveyor drives): Monthly
High-criticality equipment (fans, compressors): Quarterly
Routine equipment: Bi-annually
Emergency inspection trigger: Any alert level ≥ WARNING from AI monitoring system

2. THERMAL ANOMALY CLASSIFICATION
Class 1 – Low Risk (ΔT < 10°C above ambient):
  - Monitor on next scheduled inspection
  - No immediate action required

Class 2 – Medium Risk (ΔT 10–30°C above ambient):
  - Raise P2 work order within 24 hours
  - Re-inspect within 2 weeks after maintenance

Class 3 – High Risk (ΔT 30–60°C above ambient):
  - Raise P1 work order immediately
  - Do not operate equipment until root cause investigated

Class 4 – Critical Risk (ΔT > 60°C above ambient):
  - Emergency shutdown required
  - Follow ERP-001 emergency procedure

3. INSPECTION POINTS FOR BLAST FURNACE PUMPS
Mandatory inspection points (document all readings):
  a) Drive-end bearing housing exterior (alarm: ΔT > 20°C vs ambient)
  b) Non-drive-end bearing housing (alarm: ΔT > 15°C)
  c) Mechanical seal area (alarm: ΔT > 25°C — leakage risk)
  d) Motor stator (alarm: ΔT > 30°C — insulation degradation)
  e) Lubrication pump motor (alarm: ΔT > 20°C)
  f) Coupling guard area (alarm: ΔT > 35°C — coupling failure risk)

4. REPORTING
All thermographs must be stored in SAP PM with:
  - Timestamp, equipment ID, ambient temperature
  - Maximum, minimum, and average temperatures for each inspection point
  - ΔT classification (Class 1–4)
  - Comparison image from previous inspection (trend reference)
  - Recommended action and urgency

5. CORRELATION WITH AI PREDICTIVE SYSTEM
Thermography findings must be entered into Stelos AI for:
  - Correlation with vibration and process sensor data
  - RUL model recalibration (higher bearing temperature = lower RUL estimate)
  - Automated work order generation and priority escalation
""",
        "category": "INSPECTION_PROCEDURE",
        "equipment_type": "all",
        "fault_types": ["overheating", "bearing_failure", "seal_failure", "electrical_fault"]
    },
    {
        "id": "RISK-MATRIX-001",
        "title": "Tata Steel 5×5 Risk Assessment Matrix – Equipment Maintenance Decisions",
        "content": """
RISK ASSESSMENT FRAMEWORK – 5×5 RISK MATRIX
Document ID: RISK-MATRIX-001 | Rev: 2.0 | Effective: 2024-01-01
Authority: Chief Maintenance Officer, Tata Steel Jamshedpur

1. RISK MATRIX STRUCTURE
Likelihood (Failure Probability):
  L1: < 20% — Unlikely
  L2: 20-40% — Possible
  L3: 40-60% — Likely
  L4: 60-80% — Very Likely
  L5: > 80% — Almost Certain

Consequence (Business Impact):
  C1: Negligible — < ₹1 Lakh loss, no safety risk
  C2: Minor — ₹1–10 Lakhs loss, minor process disruption
  C3: Moderate — ₹10–50 Lakhs loss, department-level impact
  C4: Major — ₹50–200 Lakhs loss, plant-level impact, safety risk
  C5: Catastrophic — > ₹200 Lakhs loss, injury/fatality risk, regulatory action

Risk Score = Likelihood × Consequence

Risk Band and Required Action:
  LOW (1–4):    Routine maintenance, schedule in next PM cycle
  MEDIUM (5–9): Plan maintenance within 30 days, P3 work order
  HIGH (10–15): Urgent maintenance within 72 hours, P2 work order
  CRITICAL (16–25): Immediate action within 24 hours, P1 work order, management notification

2. EQUIPMENT CRITICALITY RATINGS (Tata Steel Jamshedpur)
Blast Furnace Cooling Pumps (BF-Pump-10 to 14):
  - Consequence rating: C5 (catastrophic) — blast furnace stoppage = ₹37.5 Lakhs/hour
  - Single-point failure: YES (no redundancy on BF#3 and BF#4)
  - Required reliability target: MTBF > 3,000 hours

Conveyor System (A through F):
  - Consequence rating: C4 (major) — iron ore supply disruption = ₹8 Lakhs/hour
  - Redundancy: Partial (alternative routes available for planned downtime)

Cooling Fans (Sinter Plant):
  - Consequence rating: C3 (moderate) — sinter quality degradation = ₹4 Lakhs/hour
  - Redundancy: YES (standby fans available)

3. AI-ASSISTED RISK SCORING
Stelos AI maps AI outputs to this framework:
  - Isolation Forest health index → Likelihood score (HI < 30 → L5, HI 30-50 → L4, etc.)
  - Equipment criticality rating → Consequence score
  - Final risk = L × C → Risk band → Maintenance priority (P1/P2/P3/Routine)
  - Confidence interval on RUL adjusts likelihood: wide CI → conservative (higher) likelihood score

4. ESCALATION THRESHOLDS
Automatic P1 escalation triggers:
  - Risk score ≥ 16 (CRITICAL band)
  - Failure probability > 80% on C4/C5 equipment
  - RUL < 5 days on any critical equipment
  - Two consecutive weeks of rising vibration trend on any blast furnace pump

Plant Manager notification required for:
  - Any EMERGENCY alert on blast furnace equipment
  - Any predicted production loss > ₹50 Lakhs in risk assessment
  - Any equipment where failure probability > 80% AND no maintenance slot available within 48 hours
""",
        "category": "RISK_FRAMEWORK",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "SOP-BEARING-001",
        "title": "SOP: Bearing Replacement Procedure – Centrifugal Pumps and Rotating Equipment",
        "content": """
STANDARD OPERATING PROCEDURE – BEARING REPLACEMENT
Document ID: SOP-BEARING-001 | Rev: 3.5 | Effective: 2024-02-01
Applicable Equipment: All BF Pumps, Cooling Fans, Conveyors – Jamshedpur Plant

1. REPLACEMENT TRIGGERS
Replace bearing immediately when:
- Vibration exceeds 0.70 mm/s for more than 48 continuous hours
- Bearing temperature exceeds 85°C after lubrication correction
- Oil analysis shows metal particle count > 150 ppm
- BPFI/BPFO defect frequencies detected in FFT spectrum
- RUL prediction indicates < 7 days remaining

2. PRE-REPLACEMENT REQUIREMENTS
- Raise P1 work order in SAP PM with bearing part number
- Confirm replacement bearing available in Central Store (Building 14)
- Assemble tools: bearing puller, hydraulic press, torque wrench (85 Nm), dial indicator
- Review LOTO procedure (SOP-SAFETY-001 §3) — mandatory before any physical work

3. REPLACEMENT PROCEDURE
Step 1: Initiate controlled shutdown (SOP-SHUTDOWN-001 §2)
Step 2: Apply LOTO – lock all energy isolation points, tag with personal danger lock
Step 3: Allow 30-minute cooldown before touching bearing housing
Step 4: Drain lubrication oil – collect sample for analysis (contamination evidence)
Step 5: Remove coupling using bearing puller; avoid impact on shaft
Step 6: Extract old bearing using hydraulic puller at designated puller grooves
Step 7: Clean bearing seat with lint-free cloth; check for scoring (> 0.02mm → replace shaft)
Step 8: Heat new bearing to 80°C max in oil bath (never flame); slide onto shaft immediately
Step 9: Torque bearing housing bolts to 85 Nm in cross-pattern sequence
Step 10: Fill lubrication to correct level – Shell Tellus S2 VX 46
Step 11: Re-couple shaft; verify alignment with dial indicator (TIR < 0.05mm)
Step 12: Remove LOTO; perform trial run 15 minutes at no load
Step 13: Commissioning check – vibration must be < 0.30 mm/s before handover to operations

4. POST-REPLACEMENT ACTIONS
- Log bearing serial number, installation date, and clearance measurement in SAP PM
- Set new baseline vibration and temperature in AI monitoring system
- Schedule first follow-up inspection at 72 hours and 168 hours
- Typical bearing replacement time: 4–6 hours (pump), 2–3 hours (fan)

5. BEARING SPECIFICATIONS
Pump Drive End: SKF 6315-2RS1/C3 (Rs 4,200, Central Store)
Pump Non-Drive End: SKF 6215-2RS1 (Rs 2,800)
Fan: SKF 6312-2RS1/C3 (Rs 1,800)
Conveyor Drive: SKF 22220 EK/C3 (Rs 12,500, 2-day lead time)
""",
        "category": "SOP",
        "equipment_type": "rotating_equipment",
        "fault_types": ["bearing_failure", "overheating", "vibration"]
    },
    {
        "id": "SOP-SAFETY-001",
        "title": "SOP: Lockout/Tagout (LOTO) and Permit-to-Work – Energy Isolation Safety",
        "content": """
STANDARD OPERATING PROCEDURE – LOCKOUT / TAGOUT (LOTO)
Document ID: SOP-SAFETY-001 | Rev: 4.1 | Effective: 2024-01-01
Regulatory Basis: Factories Act 1948, IS 13406, Tata Steel Safety Standard TS-SAF-007

1. PURPOSE
Ensure zero energy state before any maintenance work on rotating or electrical equipment.
LOTO violations are Category A safety offences — immediate suspension.

2. MANDATORY PPE FOR ALL MAINTENANCE WORK
Standard PPE (always required near rotating equipment):
- Steel-toe safety boots (IS 15298 compliant)
- Hard hat (IS 2925, Class B)
- High-visibility vest (retro-reflective)
- Safety gloves (minimum leather, Grade 2)
- Hearing protection (> 85 dB areas – all pump rooms)

Additional PPE by fault condition:
- EMERGENCY/CRITICAL temperature: Heat-resistant gloves (EN 407, Level 4)
- High vibration (> 0.60 mm/s): Anti-vibration gloves (EN ISO 10819)
- Lubrication oil fault: Chemical splash goggles (EN 166)
- Electrical work: Insulated gloves Class 00 minimum (500V rated)
- Hot oil/steam risk: Full face shield + chemical resistant apron

3. LOTO PROCEDURE
Step 1: Notify shift supervisor and control room of impending isolation
Step 2: Identify ALL energy sources (electrical, pneumatic, hydraulic, steam, gravity)
Step 3: Shut down equipment using normal stopping procedure
Step 4: Operate each isolation device to de-energise
Step 5: Apply personal danger lock to each isolation point
Step 6: Attach danger tag with: Name, Date, Time, Work Description
Step 7: Verify zero energy state — press start, attempt to jog; confirm no movement
Step 8: Dissipate stored energy (bleed pressure, lower suspended loads, release spring tension)
Step 9: Begin maintenance work

4. TWO-PERSON RULE
Mandatory for EMERGENCY and CRITICAL equipment:
- One person works, one person monitors and maintains line-of-sight
- Both must wear full PPE
- Buddy must be trained in emergency stop and rescue procedure

5. PERMIT-TO-WORK LEVELS
Hot Work Permit: Any grinding, welding, cutting (fire watch mandatory)
Confined Space Entry: All pump pits, sumps, vessels (atmospheric test required)
Working at Height: Any work > 1.8m above ground (full body harness required)
Electrical Isolation: LT panel work (electrical safety officer sign-off required)

6. RESTORATION AFTER MAINTENANCE
Step 1: Remove all tools and rags from work area
Step 2: Replace all guards and covers
Step 3: Remove personal danger locks (only the person who applied them)
Step 4: Remove tags and restore energy in reverse isolation sequence
Step 5: Commission test run per equipment-specific SOP
Step 6: Notify shift supervisor: work complete, equipment returned to service
""",
        "category": "SOP",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "SOP-SHUTDOWN-001",
        "title": "SOP: Controlled Equipment Shutdown and Emergency Stop Procedures",
        "content": """
STANDARD OPERATING PROCEDURE – SHUTDOWN PROCEDURES
Document ID: SOP-SHUTDOWN-001 | Rev: 3.2 | Effective: 2024-01-15
Applicable Equipment: All critical rotating equipment, Jamshedpur Plant

1. PLANNED CONTROLLED SHUTDOWN
Use when: Scheduled maintenance, RUL < 7 days, or P1/P2 work order raised.
Step 1: Inform control room and shift supervisor — get verbal confirmation
Step 2: Reduce load gradually to 50% over 5 minutes (never hard-stop under load)
Step 3: Press STOP on local panel; confirm motor current drops to zero
Step 4: Verify standby/backup equipment is running (if applicable)
Step 5: Allow 30-minute cooldown before LOTO application
Step 6: Log shutdown time, reason, and expected restart in SAP PM

2. EMERGENCY SHUTDOWN (SCRAM)
Trigger immediately if:
- Bearing temperature > 95°C (pump) / 80°C (fan)
- Vibration > 1.0 mm/s sustained > 5 minutes
- Abnormal noise (grinding, knocking, metallic scraping)
- Visible smoke, sparks, or oil fire
- Motor current > 110% nameplate for > 30 seconds

Emergency procedure:
Step 1: Press RED emergency stop button at local control panel
Step 2: Simultaneously alert shift supervisor via P.A. system
Step 3: If fire: activate CO2 suppression; evacuate 10m exclusion zone
Step 4: Do NOT restart until root cause identified and cleared by Maintenance Lead

3. RESTART AFTER UNPLANNED SHUTDOWN
Mandatory checks before restart:
- Visual inspection: no visible damage, leaks, or loose components
- Vibration check: < 0.30 mm/s on trial run
- Temperature: bearing housing < 50°C before restart attempt
- Oil level: check sight glass; top up if below 60% level
- Maintenance Lead sign-off on restart form
- Minimum restart interval: 30 minutes after emergency stop

4. BACKUP EQUIPMENT SWITCHOVER
For pumps with standby redundancy:
- Auto-switchover on alarm if configured; otherwise manual
- Confirm standby running before stopping duty equipment
- Notify control room; update plant status board
- Log switchover event with timestamp in shift log

5. ESTIMATED DOWNTIME GUIDE
Bearing replacement: 4–6 hours
Mechanical seal replacement: 2–3 hours
Impeller replacement: 6–8 hours
Lubrication system flush: 2 hours
Full pump overhaul: 24–48 hours
Emergency repair (unplanned): Add 2–4 hours for diagnosis and parts procurement
""",
        "category": "SOP",
        "equipment_type": "all",
        "fault_types": ["bearing_failure", "overheating", "vibration", "emergency"]
    },
    {
        "id": "SOP-PM-003",
        "title": "SOP: Preventive Maintenance Schedule and Logbook Requirements",
        "content": """
STANDARD OPERATING PROCEDURE – PREVENTIVE MAINTENANCE SCHEDULING
Document ID: SOP-PM-003 | Rev: 2.6 | Effective: 2024-04-01
Applicable to: All rotating equipment maintenance teams, Jamshedpur Plant

1. PM SCHEDULE OVERVIEW
Hourly (operator): Visual inspection, check for unusual noise/vibration/leaks
Shift (8 hours): Record sensor readings in Maintenance Logbook (this document §4)
Daily: Lubrication oil level check, belt tension check, coupling guard inspection
Weekly (SOP-VIBRATION-001): Portable vibration analyser readings on all drive ends
Monthly: Infrared thermography (INSPECTION-IR-001), oil sampling and analysis
Quarterly: Full PM inspection per equipment-specific SOP
Annually: Major overhaul assessment, impeller clearance measurement

2. SENSOR MONITORING INTERVALS BY ALERT LEVEL
EMERGENCY: Continuous monitoring; operator must be present
CRITICAL: Every 2 hours; readings logged; shift supervisor notified each cycle
WARNING: Every 4 hours; trends reviewed at end of shift
NORMAL: Every 8 hours (standard shift check)

Alert escalation — immediate notification to:
- Shift supervisor: any transition to WARNING or above
- Maintenance manager: any CRITICAL alert
- Plant manager: any EMERGENCY alert or predicted RUL < 24 hours

3. PREDICTIVE MAINTENANCE TRIGGERS (Stelos AI)
Stelos AI system generates work orders automatically for:
- Health Index drop > 15 points in 24 hours
- Failure probability crossing 40% threshold (P3 work order)
- Failure probability crossing 70% threshold (P2 work order, immediate review)
- Failure probability crossing 85% threshold (P1 work order, EMERGENCY)
- RUL < 14 days (schedule maintenance within current cycle)
- RUL < 5 days (immediate maintenance required)

4. LOGBOOK REQUIREMENTS
Every shift, technician must record for each monitored equipment:
- Timestamp, technician name and badge number
- Sensor readings: temperature, vibration, pressure, oil temp, motor current
- Observations: noise, leaks, unusual behaviour
- Actions taken (if any)
- Alert level and any changes from previous shift

Logbook format (SAP PM + physical backup):
- Digital entry in SAP PM within 30 minutes of reading
- Physical logbook (Building 14, Maintenance Office) as backup
- Discrepancies between digital and physical must be flagged to supervisor

5. KEY PERFORMANCE INDICATORS
MTBF target (blast furnace pumps): > 3,000 hours
Planned maintenance ratio target: > 80% of all maintenance events
PM compliance rate target: > 95% of scheduled PMs completed on time
Unplanned downtime target: < 15 hours/quarter per plant section
""",
        "category": "SOP",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "SOP-MOTOR-001",
        "title": "SOP: Electric Motor Condition Monitoring and Maintenance",
        "content": """
STANDARD OPERATING PROCEDURE – ELECTRIC MOTOR MAINTENANCE
Document ID: SOP-MOTOR-001 | Rev: 2.4 | Effective: 2024-03-01
Applicable Equipment: All AC induction motors driving rotating equipment, Jamshedpur

1. MOTOR HEALTH PARAMETERS
Normal current draw: 85–105% of nameplate FLA
Warning current: > 105% FLA sustained > 10 minutes
Critical current: > 110% FLA or < 70% FLA (open phase)
Winding temperature: < 120°C (Class F insulation, alarm at 130°C)
Insulation resistance: > 100 MΩ (alarm < 10 MΩ, replace < 1 MΩ)
Bearing temperature (motor): < 80°C (alarm at 85°C)

2. ELEVATED CURRENT CAUSES AND ACTIONS
Motor current > 110% nameplate FLA:
- Cause 1: Mechanical overload (shaft misalignment, bearing seizure, pump cavitation)
  Action: Check alignment (SOP-ALIGNMENT-001), inspect bearing, reduce pump load
- Cause 2: Electrical fault (single-phasing, voltage imbalance > 2%)
  Action: Check voltage at MCC terminals; notify electrical team
- Cause 3: Rotor fault (broken rotor bars)
  Detection: Current signature analysis (MCSA) — look for sidebands at ±2sf around fundamental
  Action: Schedule motor replacement at next planned shutdown

Motor current < 80% nameplate (sudden drop):
- Likely cause: Coupling failure, belt breakage, impeller detachment
- Action: Immediate shutdown; inspect mechanical connection

3. INSULATION AND WINDING CHECKS
Annual Megger test (500V DC for LT motors):
- > 100 MΩ: Healthy
- 10–100 MΩ: Monitor closely; plan rewinding
- 1–10 MΩ: Schedule rewinding within 30 days
- < 1 MΩ: Do not energise; rewind immediately

4. MOTOR REPLACEMENT CRITERIA
Replace motor when:
- Insulation resistance < 1 MΩ (Class F)
- Winding temperature consistently > 130°C under normal load
- Repair cost > 65% of replacement cost (economic replacement rule)
- Motor age > 20 years for critical service (blast furnace pumps)

5. SPARE MOTOR INVENTORY
45 kW, 4-pole TEFC (BF Pump duty): 1 unit spare (Central Store)
22 kW, 4-pole TEFC (Conveyor drive): 1 unit spare
11 kW, 4-pole TEFC (Cooling fan): 2 units spare
Lead time for non-stocked motors: 14–21 days (BHEL / Siemens India)
""",
        "category": "SOP",
        "equipment_type": "motor",
        "fault_types": ["electrical_fault", "overload", "bearing_failure", "winding_failure"]
    },
    {
        "id": "SOP-ROLLING-MILL-001",
        "title": "SOP: Hot Rolling Mill Maintenance and Roll Change Procedure",
        "content": """
STANDARD OPERATING PROCEDURE – HOT ROLLING MILL MAINTENANCE
Document ID: SOP-ROLLING-001 | Rev: 1.8 | Effective: 2024-06-01
Applicable Equipment: Rolling-Mill — Hot Rolling Section, Jamshedpur Plant

1. NORMAL OPERATING PARAMETERS
- Roll bearing temperature: 55–85°C (alarm at 90°C, shutdown at 100°C)
- Vibration (rolling mill stand): < 0.45 mm/s RMS
- Hydraulic pressure (screwdown): 180–220 bar
- Roll gap: ± 0.05mm tolerance (automated AGC)
- Motor current (main drive): 85–105% FLA

2. ROLL CHANGE PROCEDURE
Trigger: Roll wear > 0.8mm diameter difference, or surface crack detected
Estimated time: 4 hours (experienced crew of 4)
Step 1: Complete current rolling campaign; do not interrupt mid-billet
Step 2: Cool roll to < 60°C surface temperature
Step 3: Apply LOTO on main drive and hydraulic unit (SOP-SAFETY-001 §3)
Step 4: Release roll gap using manual hydraulic; lower roll onto change carriage
Step 5: Withdraw using roll-change carriage (monorail)
Step 6: Install new roll; verify gap to within ±0.02mm
Step 7: Commission: run at 20% speed; check bearing temp and vibration

3. BEARING MAINTENANCE SPECIFICS
Roll neck bearings (4-row tapered roller): Replace every 6,000 rolling hours
Chock bearing housings: Clean and inspect each roll change
Bearing clearance: 0.12–0.18mm radial (replace if > 0.25mm)
Lubrication: Grease-lubricated, repack every roll change (Mobilux EP2)

4. CRITICAL ALARM RESPONSES
Cobble (strip jam):
- Immediate: Emergency stop all drives
- Isolate pinch rolls; cut strip at entry table
- Cool area before inspection; check roll surface for damage

Roll crack detected (eddy current):
- Withdraw roll immediately regardless of campaign schedule
- Send for NDT inspection; do not reuse until cleared
- Log defect location and depth in SAP PM

5. FINANCIAL CONTEXT
Production rate: 80 tons/hour at full speed
Unplanned downtime cost: ₹12 Lakhs/hour
Planned roll change (budgeted): ₹3.2 Lakhs (rolls + labour)
Emergency roll change: ₹8.5 Lakhs (premium parts + overtime)
""",
        "category": "SOP",
        "equipment_type": "mill",
        "fault_types": ["bearing_failure", "roll_wear", "vibration", "hydraulic_fault"]
    },
    {
        "id": "SOP-BLAST-FURNACE-001",
        "title": "SOP: Blast Furnace Auxiliary Equipment Maintenance – Cooling and Blower Systems",
        "content": """
STANDARD OPERATING PROCEDURE – BLAST FURNACE AUXILIARY MAINTENANCE
Document ID: SOP-BF-001 | Rev: 2.9 | Effective: 2024-05-15
Applicable Equipment: Blast-Furnace #1–#4 Cooling and Gas Handling Systems, Jamshedpur

1. CRITICALITY CONTEXT
Blast furnace cooling system failure = furnace campaign interruption
Cost of unplanned BF shutdown: ₹37.5 Lakhs/hour (production loss alone)
Relining cost if thermal excursion damages staves: ₹150–300 Crores
Risk classification: C5 Catastrophic (RISK-MATRIX-001)

2. COOLING WATER PUMP REQUIREMENTS
Operating parameters (BF cooling circuit):
- Flow rate: 1,800–2,200 m³/hour per BF
- Pressure: 4.5–5.5 bar at header
- Temperature rise across BF: < 8°C (alarm at 10°C)
- Pump efficiency: > 82% (alarm < 75%)
- Bearing temperature: < 75°C (alarm 80°C, trip 90°C)

Mandatory redundancy: Minimum 1 standby pump ready to auto-start on duty pump failure
Switchover time target: < 30 seconds (auto-start system)
Manual switchover: < 2 minutes

3. HOT BLAST BLOWER MAINTENANCE
Normal vibration: < 0.35 mm/s at 3,600 RPM
Bearing replacement interval: 8,000 hours or vibration > 0.50 mm/s
Blade inspection: Every 6 months (erosion due to hot gas carry-over)
Inlet filter differential pressure: < 50 mbar (alarm at 75 mbar)

4. HIGH-TEMPERATURE OPERATING PRECAUTIONS
Equipment near cast house (ambient > 60°C):
- Bearing lubrication interval halved (high-temperature lube degradation)
- Infrared inspection monthly (vs quarterly for standard areas)
- Additional cooling by portable fans if ambient > 70°C

5. EMERGENCY RESPONSE — COOLING PUMP FAILURE
Step 1: Auto-start standby pump (confirmed within 30 seconds)
Step 2: If standby fails to start — initiate BF cast immediately to reduce thermal load
Step 3: Reduce hot blast rate by 30% within 2 minutes
Step 4: Notify BF manager and Plant Director — BF campaign at risk
Step 5: Emergency procurement of pump from stores (SOP-SPARE-001)
Target repair time: < 4 hours (bearing) | < 8 hours (seal) | < 24 hours (major overhaul)
""",
        "category": "SOP",
        "equipment_type": "furnace",
        "fault_types": ["cooling_failure", "bearing_failure", "overheating", "flow_loss"]
    },
    {
        "id": "BENCHMARK-INDUSTRY-001",
        "title": "Industry Benchmark Data: Steel Plant Equipment Reliability – ISO Standards",
        "content": """
INDUSTRY BENCHMARK REFERENCE DOCUMENT
Document ID: BENCHMARK-001 | Rev: 1.2 | Effective: 2024-01-01
Source: World Steel Association, EPRI, ISO 10816-3, Tata Steel Internal KPI Data

1. VIBRATION BENCHMARKS (ISO 10816-3, Machines 15-300 kW)
Zone A (New equipment, continuous operation acceptable): < 0.28 mm/s RMS
Zone B (Acceptable long-term): 0.28 – 0.71 mm/s RMS
Zone C (Unsatisfactory long-term, corrective within 30 days): 0.71 – 1.8 mm/s RMS
Zone D (Danger, immediate shutdown): > 1.8 mm/s RMS

Tata Steel internal alarm setpoints (more conservative):
Pump: Alert 0.50 | Alarm 0.70 | Trip 1.0 mm/s
Fan: Alert 0.35 | Alarm 0.45 | Trip 0.60 mm/s
Conveyor drive: Alert 0.40 | Alarm 0.55 | Trip 0.80 mm/s
Rolling mill: Alert 0.40 | Alarm 0.50 | Trip 0.70 mm/s

2. TEMPERATURE BENCHMARKS
Pump bearing (normal service): 55–75°C
Pump bearing (hot process): 65–85°C
Motor winding: < 120°C (Class F insulation)
Lubrication oil: 45–65°C (alarm 70°C, shutdown 80°C)
Fan bearing: 40–60°C (alarm 70°C, shutdown 80°C)

3. MTBF BENCHMARKS (WORLD STEEL DATA)
Blast furnace cooling pumps: 2,500–3,500 hours (Tata Steel target: 3,000 hrs)
Industrial conveyors (heavy duty): 3,000–4,000 hours
Cooling fans (sinter plant): 4,000–6,000 hours
Rolling mill main drives: 5,000–8,000 hours
Hot blast blowers: 6,000–10,000 hours

Tata Steel Jamshedpur current MTBF (Q3 2024): 2,840 hours (below 3,000 target)
Industry top quartile MTBF (blast furnace pumps): 3,800 hours

4. FINANCIAL BENCHMARKS (TATA STEEL INTERNAL)
Average unplanned downtime cost: ₹28 Lakhs/day across all equipment
Blast furnace specific: ₹37.5 Lakhs/hour
Conveyor system: ₹8 Lakhs/hour
Cooling fan failure: ₹4 Lakhs/hour

Planned vs emergency maintenance cost ratio: 1:5 (industry average)
PM compliance impact: Each 10% increase in PM compliance → 7% reduction in unplanned downtime

5. OEE BENCHMARKS FOR STEEL PLANTS
World-class OEE: > 85%
Industry average: 72–78%
Tata Steel target: > 83%
Availability (target): > 95%
Performance (target): > 92%
Quality (target): > 98.5%

6. PREDICTIVE MAINTENANCE ROI
Industry average: ₹4–8 saved per ₹1 invested in PdM program
Condition monitoring ROI: Typical payback period 12–18 months
AI-based PdM additional ROI: +30–50% over traditional CBM programs
False positive rate (best-in-class AI systems): < 5%
""",
        "category": "BENCHMARK",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "FAR-2024-Q4-SUMMARY",
        "title": "Failure Analysis Summary: Q4 2024 Critical Equipment Failures",
        "content": """
FAILURE ANALYSIS QUARTERLY SUMMARY – Q4 2024
Document ID: FAR-Q4-2024 | Date: 2025-01-10 | Plant: Jamshedpur
Equipment Category: All critical rotating equipment

SUMMARY OF Q4 2024 UNPLANNED FAILURES

FAILURE #1: Rolling-Mill Main Drive Bearing (2024-10-15)
Root Cause: Lubrication starvation during 14-day production run without scheduled PM
Warning Signs Missed: Motor current rose 8% over 3 days; vibration at 0.62 mm/s
Downtime: 14 hours | Loss: ₹1.68 Crores
Lesson: Current signature trending is early indicator of mechanical overload

FAILURE #2: Cooling-Fan-2 V-Belt Failure (2024-11-03)
Root Cause: Belt age 9 months (exceeded 8,000-hour life); dust accelerated wear
Warning Signs: Vibration asymmetry increased 22% over 2 weeks
Downtime: 3 hours | Loss: ₹1.2 Lakhs (standby fan available)
Lesson: Belt inspection must use vibration asymmetry ratio, not visual alone

FAILURE #3: Compressor-2 Seal Failure (2024-11-28)
Root Cause: Oil contamination from upstream filtration fault — abrasive particles in seal faces
Warning Signs: Oil temperature rose 6°C over 10 days; slight pressure drop
Downtime: 7 hours | Loss: ₹38 Lakhs (oxygen plant supply interrupted)
Lesson: Upstream oil quality monitoring is leading indicator for seal life

FAILURE #4: Blast-Furnace Tuyere Cooling Pump (2024-12-19)
Root Cause: Impeller wear (clearance 1.8mm vs 0.5mm design) causing cavitation
Warning Signs: Discharge pressure dropped 12 PSI over 6 weeks; vibration broadband increase
Downtime: 11 hours | Loss: ₹4.1 Crores (BF ramp-down required)
Lesson: Discharge pressure trending is the most sensitive early indicator for impeller wear

Q4 2024 RELIABILITY METRICS
Total unplanned downtime: 35 hours (target: < 15 hours) — MISSED TARGET
Estimated loss from all failures: ₹7.2 Crores
Estimated preventable portion: ₹5.8 Crores (80% — detectable with AI monitoring)
AI prediction accuracy on Q4 events (post-hoc): 4 of 4 failures were predictable > 7 days ahead

RECOMMENDATIONS FOR Q1 2025
1. Deploy Stelos AI across all 4 blast furnaces — BF#2 and #4 currently unmonitored
2. Implement discharge pressure trending alert in compressor circuit
3. Reduce belt inspection interval for high-dust fans to 4 weeks
4. Mandatory P1 escalation for any discharge pressure drop > 8 PSI from baseline
""",
        "category": "FAILURE_REPORT",
        "equipment_type": "all",
        "fault_types": ["bearing_failure", "lubrication_failure", "seal_failure", "impeller_wear"]
    },
    {
        "id": "SOP-PPE-MATRIX-001",
        "title": "PPE Requirements Matrix – Maintenance Activities by Equipment and Alert Level",
        "content": """
PPE REQUIREMENTS REFERENCE – MAINTENANCE ACTIVITIES
Document ID: SOP-PPE-001 | Rev: 2.0 | Effective: 2024-02-15
Authority: Plant Safety Officer, Jamshedpur | Basis: IS 4770, IS 15298, EN 166, EN 374

1. STANDARD PPE (ALL MAINTENANCE ACTIVITIES – NO EXCEPTIONS)
Every technician entering equipment areas must wear:
✓ Steel-toe safety boots (IS 15298-1:2016, S3 rating minimum)
✓ Hard hat (IS 2925:1984, Class B – electrical protection)
✓ High-visibility safety vest (retro-reflective, ANSI Class 2 minimum)
✓ Safety gloves (leather work gloves, Grade 2 cut resistance)
✓ Safety spectacles (ANSI Z87.1 / EN 166)

2. HEARING PROTECTION (MANDATORY IN HIGH-NOISE AREAS)
Threshold: > 85 dB(A) — all pump rooms, compressor areas, near blast furnaces
Disposable foam earplugs: All areas 85–95 dB(A)
Earmuffs (SNR > 25 dB): Areas > 95 dB(A) — hot blast blowers, rolling mill main drives

3. ADDITIONAL PPE BY FAULT CONDITION
Elevated Temperature Fault (bearing temp > 85°C or CRITICAL/EMERGENCY):
+ Heat-resistant gloves EN 407: Level 4 contact heat protection
+ Thermal flash goggles (not standard spectacles)
+ Stay minimum 1m from bearing housing until temp drops below 70°C

High Vibration (> 0.60 mm/s):
+ Anti-vibration gloves ISO 10819: reduce HAVS (Hand-Arm Vibration Syndrome) exposure
+ Limit continuous contact time to 30 minutes per session

Lubrication Oil Fault (oil temp > 65°C, seal failure suspected):
+ Chemical splash goggles (EN 166, Grade 3)
+ Nitrile chemical-resistant gloves (EN 374, Type B minimum)
+ Apron if seal face inspection required

Electrical Work (motor > 415V):
+ Insulated rubber gloves Class 00 (500V rated) over cotton inner gloves
+ Rubber-soled boots with electrical insulation rating
+ Face shield for any live panel work

4. PPE BY EQUIPMENT TYPE
Blast Furnace Area (ambient > 60°C, radiant heat):
+ Heat-reflective aluminised jacket if within 5m of cast house during tapping
+ Tinted face shield (welding shade #3 or higher during casting)

Rolling Mill:
+ Leather spats (ankle/lower leg protection from mill scale)
+ Full arm protection (fire-resistant coveralls, not standard uniform)

Conveyor Belt Work:
+ Tag line required if working near moving belt within 1m
+ No loose clothing, jewellery, or untied hair — entanglement risk

5. EXCLUSION ZONES BY ALERT LEVEL
EMERGENCY: 5-metre exclusion zone — only authorised persons with full PPE
CRITICAL: 2-metre buffer — two-person rule applies
WARNING: Standard PPE, no restriction on proximity
NORMAL: Standard PPE
""",
        "category": "SOP",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "SOP-COMPRESSOR-001",
        "title": "SOP: Air Compressor Condition Monitoring – Oxygen Plant and Instrument Air",
        "content": """
STANDARD OPERATING PROCEDURE – COMPRESSOR MAINTENANCE
Document ID: SOP-COMP-001 | Rev: 1.6 | Effective: 2024-07-01
Applicable Equipment: Compressor-2 (Oxygen Plant), Instrument Air Compressors, Jamshedpur

1. OPERATING PARAMETERS
Discharge pressure: 7.5–8.5 bar (alarm < 7.0, > 9.0)
Interstage pressure: 2.4–2.8 bar
Bearing temperature: 55–80°C (alarm 85°C, trip 95°C)
Vibration: < 0.40 mm/s (alarm 0.55, trip 0.70)
Oil temperature: 50–70°C (alarm 75°C)
Oil pressure: 2.0–3.5 bar (alarm < 1.5 bar)
Motor current: 85–105% FLA

2. COMPRESSOR-SPECIFIC FAULTS
Valve Failure (most common fault):
- Symptoms: discharge pressure fluctuation ± 0.5 bar, increased current draw, elevated discharge temperature
- Cause: Carbon deposits, liquid carry-over, valve spring fatigue
- Detection: Pressure ratio monitoring; vibration frequency signature (valve frequency = RPM × number of cylinders)
- Action: Valve inspection every 4,000 hours; replace if leakage > 5%

Piston Ring Wear:
- Symptoms: Oil carry-over in discharge air/gas, loss of compression efficiency
- Detection: Discharge oil content analyser (alarm > 5 ppm oil in gas)
- Action: Replace piston rings every 8,000 hours or when efficiency drops > 8%

Shaft Seal Deterioration:
- Symptoms: Gas leakage at shaft exit (detectable with snoop solution or gas detector)
- Action: Replace mechanical seal during next planned PM; emergency if leakage rate > 50 SLPM

3. MONITORING SCHEDULE
Continuous: Discharge pressure, bearing temperatures, vibration (online sensors)
Shift: Record all parameters in logbook (SOP-PM-003 §4)
Weekly: Oil analysis sample (send to laboratory)
Monthly: Valve leakage test, filter element differential pressure check
6-monthly: Piston ring inspection, all seals inspection
Annual: Full overhaul — valves, rings, bearings, seals

4. OXYGEN PLANT CRITICALITY
Compressor-2 supplies oxygen to BF and SMS (Steel Melting Shop)
Failure impact: Oxygen supply interruption → BF production reduction 15–20% within 2 hours
Standby: Compressor-1 (capacity 70% of Compressor-2; adequate for emergency)
Switchover: < 5 minutes (manual valve + motor start)
""",
        "category": "SOP",
        "equipment_type": "compressor",
        "fault_types": ["valve_failure", "seal_failure", "bearing_failure", "oil_contamination"]
    },
    {
        "id": "ENERGY-AUDIT-001",
        "title": "Energy Efficiency and Asset Health Correlation – Steel Plant Rotating Equipment",
        "content": """
ENERGY AUDIT AND EFFICIENCY REPORT
Document ID: ENERGY-001 | Rev: 1.0 | Effective: 2024-09-01
Scope: All rotating equipment > 15 kW, Jamshedpur Plant

1. EQUIPMENT HEALTH vs ENERGY CONSUMPTION
Degraded bearings (vibration 0.50–0.70 mm/s):
- Additional power consumption: 3–8% above baseline
- Monthly energy waste: ~₹85,000 per pump (based on Rs 7.5/kWh industrial tariff)
- Combined fleet impact: If 3 pumps in WARNING: ~₹2.5 Lakhs/month wasted

Impeller wear (clearance > 1.0mm):
- Efficiency loss: 8–15% (more power for same flow)
- To maintain process flow, motor draws 10–18% excess current
- Monthly waste for single pump: ₹1.2 Lakhs

Misalignment (parallel offset > 0.05mm):
- Additional bearing load: 15–25% increase
- Power loss: 2–5% in coupling + bearing friction
- Also reduces bearing life by 30–50%

2. ENERGY-BASED DEGRADATION DETECTION
Power = Torque × Speed
Increase in motor current at constant speed = increase in torque = mechanical resistance
Early degradation signature:
- Phase 1: Current baseline shifts up 3–5% (lubrication degradation, early bearing wear)
- Phase 2: Current increase 5–10% + vibration begins rising (accelerating wear)
- Phase 3: Current > 10% + temperature rise + vibration alarm (imminent failure)

Motor current trending is often 2–3 weeks ahead of temperature or vibration alarms.

3. OEE IMPACT OF MAINTENANCE STATE
Availability = Uptime / (Uptime + Downtime)
Equipment in WARNING state: Estimated availability reduction 2–4% (higher unplanned risk)
Equipment in CRITICAL state: Estimated availability reduction 8–15%
Best-in-class predictive maintenance: Availability > 97%

OEE formula: OEE = Availability × Performance × Quality
Quality impact of degraded pumps: Flow reduction → process quality deviation → yield loss
Financial impact: 1% OEE improvement = ~₹45 Lakhs/quarter for Jamshedpur BF complex

4. CARBON FOOTPRINT
Each kWh of avoidable waste energy = 0.82 kg CO2 (Indian grid emission factor, 2024)
Fleet-wide PdM programme energy saving estimate: 2.8 MWh/day
Annual CO2 reduction: 840 tonnes CO2e
ESG reporting value: Documented contribution to Tata Steel's Net Zero 2045 target
""",
        "category": "TECHNICAL_GUIDE",
        "equipment_type": "all",
        "fault_types": ["efficiency_loss", "bearing_wear", "impeller_wear", "misalignment"]
    },
    {
        "id": "COOLING-SYSTEM-001",
        "title": "Cooling System Maintenance – Blast Furnace and Steel Melting Shop",
        "content": """
COOLING SYSTEM MAINTENANCE GUIDE
Document ID: COOLING-001 | Rev: 2.1 | Effective: 2024-04-01
Applicable: Cooling-Fan-4 (Sinter Plant), Cooling-Unit (SMS), BF Cooling Circuit

1. COOLING SYSTEM OVERVIEW
Blast Furnace Cooling: Closed-circuit water cooling, 1,800–2,200 m³/hour per BF
Steel Melting Shop: Open circuit cooling towers + closed circuit heat exchangers
Sinter Plant Cooling Fans: Forced-draft cooling for sinter strand discharge

Critical cooling parameters:
- Cooling water temperature rise across BF: < 8°C (trip at 12°C — stave damage risk)
- Cooling fan airflow: 18,000–22,000 m³/hour (alarm < 16,000 m³/hour)
- Cooling unit flow: 450–550 m³/hour (alarm < 400 m³/hour)

2. COOLING FAN MAINTENANCE (COOLING-FAN-4 SPECIFIC)
Operating zone: Sinter Plant discharge area (ambient 45–65°C)
Effect on bearing life: Each 10°C above 40°C ambient halves bearing grease life
Standard grease interval: 500 hours → Adjusted for high ambient: 250 hours
Standard bearing life: 40,000 hours → Effective life at 60°C ambient: ~15,000 hours

Blade fouling in sinter plant environment:
- Sinter dust accumulates on blade trailing edges within 3–4 weeks
- Mass imbalance from fouling: vibration increase 0.08–0.15 mm/s
- Cleaning interval: Every 4 weeks (blade wash with compressed air)
- Cleaning time: 45 minutes (requires shutdown and LOTO)

3. COOLING-UNIT (STEEL MELTING SHOP) MAINTENANCE
This unit serves liquid steel handling — criticality: C4 (Major)
Failure: Heat soak in SMS, equipment protection trips, EAF production interruption
MTBF target: > 4,000 hours

Specific fault indicators:
- Flow reduction > 10%: Check strainer, inspect impeller
- Temperature rise at outlet > 5°C from baseline: Check heat exchanger fouling
- Motor current increase > 5% at constant flow: Bearing or seal issue

4. WATER QUALITY REQUIREMENTS
Closed-circuit cooling water chemistry (BF circuit):
- pH: 7.5–9.0
- Conductivity: < 2,000 µS/cm
- Chloride: < 100 ppm (stress corrosion risk on stainless headers)
- Inhibitor (Nalco 3DT265): 200–250 ppm residual

Out-of-spec cooling water causes:
- Corrosion of cooling staves (replacement cost ₹150+ Crores)
- Scale buildup on heat transfer surfaces (efficiency reduction 15–25%)
- Accelerated pump seal deterioration (abrasive particles)
Sample frequency: Weekly; dosing system: automated continuous
""",
        "category": "SOP",
        "equipment_type": "fan",
        "fault_types": ["cooling_failure", "bearing_failure", "fouling", "flow_loss"]
    },
    {
        "id": "AI-SYSTEM-GUIDE-001",
        "title": "Stelos AI System User Guide – Agentic Predictive Maintenance Platform",
        "content": """
STELOS AI — SYSTEM GUIDE AND DECISION SUPPORT REFERENCE
Document ID: AI-GUIDE-001 | Rev: 1.0 | Effective: 2026-01-01
Platform: Stelos AI, Tata Steel Hackathon 2026 Solution

1. SYSTEM ARCHITECTURE
Stelos AI operates a 6-agent LangGraph pipeline for every maintenance query:

Agent 1 – Diagnostic Agent
Tools: Isolation Forest anomaly detector + XGBoost classifier (trained on AI4I 2020 dataset, AUC 0.9931)
Function: Classifies alert level (NORMAL/WARNING/CRITICAL/EMERGENCY) from sensor data
Output: Health score 0–100, failure probability, predicted failure type (TWF/HDF/PWF/OSF), SHAP explanation

Agent 2 – Knowledge Retrieval Agent
Tool: FAISS vector store with HuggingFace all-MiniLM-L6-v2 embeddings
Function: Semantic search over 30 Tata Steel SOPs, failure reports, and maintenance guides
Output: Top-k relevant document excerpts with relevance scores

Agent 3 – Root Cause Agent
Tool: LLM reasoning over sensor evidence + retrieved SOP context
Function: Identifies primary failure mechanism and causal chain
Mechanisms: lubrication_failure | bearing_wear | mechanical_imbalance | impeller_wear | thermal_overload | electrical_fault

Agent 4 – Predictive Maintenance Agent
Tool: Weibull degradation physics model
Function: Estimates RUL (days) with 80% CI, generates SOP-referenced work orders
Output: RUL point estimate + [lower, upper] bounds + prioritised work orders (P1/P2/P3/Routine)

Agent 5 – Business Impact Agent
Function: Financial exposure calculation in ₹ INR
Output: Production loss exposure, ROI of preventive action, spares procurement urgency

Agent 6 – Executive Intelligence Agent
Tool: Groq LLaMA-3.1-8b-instant LLM
Function: Synthesises all agent outputs into a focused, natural-language answer
Response is tailored to the specific question asked (RUL, cost, PPE, shutdown, root cause, etc.)

2. HOW TO INTERPRET OUTPUTS
Health Score: 0 = imminent failure; 100 = perfect condition
Failure Probability: 0–100%; action recommended at > 40%
RUL: Point estimate with 80% confidence interval (e.g., 5.2 days [3.1–7.8 days])
SHAP values: Positive = pushes toward failure; negative = away from failure
Confidence score: 0.60–0.97; reflects evidence strength and RAG hit quality

3. QUESTION TYPES SUPPORTED (AI COPILOT)
The system recognises and provides specialised responses for:
RUL/failure timing, cost and ROI analysis, PPE requirements, shutdown procedures,
root cause analysis, recommended maintenance actions, spare parts inventory,
monitoring frequency, safety assessment, equipment benchmarking, diagnosis/status

4. LIMITATIONS AND ESCALATION
This system is a decision support tool — it does not replace engineering judgment.
All EMERGENCY recommendations require Maintenance Lead confirmation before action.
Model retraining occurs when feedback (thumbs down) accumulates > 5 negative responses on a pattern.
For novel failure modes not in training data, confidence score drops below 0.70 — escalate to specialist.
""",
        "category": "TECHNICAL_GUIDE",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "SOP-HYDRAULIC-001",
        "title": "SOP: Hydraulic System Maintenance – Rolling Mill Press Cylinders",
        "content": """
STANDARD OPERATING PROCEDURE – HYDRAULIC SYSTEM MAINTENANCE
Document ID: SOP-HYDRAULIC-001 | Rev: 2.1 | Effective: 2024-03-01
Applicable Equipment: RM-HYD-01 through RM-HYD-08 (Jamshedpur Rolling Mill)

1. PURPOSE
Defines inspection, maintenance, and corrective procedures for hydraulic systems
powering rolling mill press cylinders and screw-down mechanisms.

2. NORMAL OPERATING PARAMETERS
- System Pressure: 180 – 220 bar (alarm at 230 bar, shutdown at 250 bar)
- Oil Temperature: 40°C – 55°C (alarm at 60°C)
- Oil Cleanliness: ISO 4406 Class 16/14/11 or better
- Flow Rate: 120 – 150 L/min at full load
- Cylinder Leakage: < 5 mL/min past seals

3. FAULT INDICATORS AND RESPONSE
Pressure Drop (< 180 bar):
  - Cause: Pump wear, relief valve leak, cylinder seal failure, line rupture
  - Action: Check pump output pressure at test point TP-01, inspect all cylinder rod seals
  - Corrective: Replace pump cartridge (P/N HYD-CART-220), reseal cylinder (P/N SEAL-KIT-85)

High Oil Temperature (> 60°C):
  - Cause: Cooler fouling, excessive back pressure, high cycle rate
  - Action: Clean plate heat exchanger, verify cooling water flow > 8 L/min
  - Corrective: Flush cooler with descaling solution, replace thermostat

Oil Contamination (particle count > Class 18):
  - Cause: Ingression from cylinder rod seals, water intrusion, worn pump
  - Action: Sample oil via port SP-03, send to lab for ISO count
  - Corrective: Replace 10-micron return filter (P/N FILT-HYD-10), flush reservoir

4. MAINTENANCE SCHEDULE
- Oil sampling: Monthly (ISO cleanliness class check)
- Filter replacement: Every 2,000 hours or quarterly
- Full oil change: Every 8,000 hours with flush
- Cylinder seal inspection: Every 4,000 hours
- Pressure relief valve test: Semi-annually at 250 bar setpoint

5. SAFETY
Follow LOTO procedure SOP-SAFETY-001 §3 before any hydraulic work.
Depressurise system fully — verify zero pressure on gauge PG-HYD-01 before opening any line.
""",
        "category": "SOP",
        "equipment_type": "hydraulic",
        "fault_types": ["pressure_drop", "overheating", "oil_contamination"]
    },
    {
        "id": "SOP-GEARBOX-001",
        "title": "SOP: Gearbox Inspection and Oil Change – Conveyor Drive Units",
        "content": """
STANDARD OPERATING PROCEDURE – GEARBOX MAINTENANCE
Document ID: SOP-GEARBOX-001 | Rev: 3.0 | Effective: 2024-02-15
Applicable Equipment: CV-GBOX-01 through CV-GBOX-12 (Raw Material Conveyors)

1. PURPOSE
Covers inspection, oil change, and corrective maintenance for helical/bevel gearboxes
driving raw material conveyors in ore handling and sinter plant areas.

2. NORMAL OPERATING PARAMETERS
- Gear Oil Temperature: 60°C – 85°C (alarm at 90°C)
- Vibration: < 2.5 mm/s RMS at gearbox housing
- Oil Level: Between MIN/MAX sight glass marks
- Input Speed: 1,480 RPM ± 5%
- Output Torque: Per nameplate (overload trip at 115%)

3. FAULT INDICATORS
High Gearbox Temperature (> 90°C):
  - Cause: Low oil level, contaminated oil, blocked breather, overload
  - Action: Check oil level via sight glass, verify breather vent is clear
  - Corrective: Change oil immediately (grade ISO VG 220), clean/replace breather

Abnormal Noise (grinding, whining):
  - Cause: Gear tooth damage, bearing failure, foreign body ingression
  - Action: Take oil sample for metal particle analysis
  - Corrective: Inspect gears via inspection cover, replace damaged gear set

Oil Leakage:
  - Cause: Worn shaft seals, damaged gaskets, overfill
  - Action: Identify leak source, check oil level
  - Corrective: Replace lip seals (P/N SEAL-GBOX-40), re-gasket inspection covers

4. OIL CHANGE PROCEDURE
- Drain oil via bottom plug while warm (50–60°C) into approved drum
- Flush with 20% fill of flushing oil, run 30 minutes at no load, drain
- Refill with ISO VG 220 synthetic gear oil to MAX mark
- Log oil change in CMMS with volume and batch number

5. MAINTENANCE INTERVALS
- Oil level check: Weekly
- Oil sample analysis: Every 3 months
- Oil change: Every 5,000 hours or annually
- Full inspection (gears, bearings, seals): Every 10,000 hours
""",
        "category": "SOP",
        "equipment_type": "gearbox",
        "fault_types": ["overheating", "abnormal_noise", "oil_leakage"]
    },
    {
        "id": "SOP-COUPLING-001",
        "title": "SOP: Flexible Coupling Inspection and Replacement",
        "content": """
STANDARD OPERATING PROCEDURE – FLEXIBLE COUPLING MAINTENANCE
Document ID: SOP-COUPLING-001 | Rev: 1.8 | Effective: 2023-11-01
Applicable Equipment: All motor-driven rotating equipment at Jamshedpur Plant

1. PURPOSE
Defines procedures for inspecting, aligning, and replacing flexible couplings
on motor-to-gearbox and motor-to-pump drive trains.

2. COUPLING TYPES IN USE
- Jaw/Spider couplings: Conveyor drives ≤ 45 kW
- Grid couplings: Pumps and fans 45–250 kW
- Disc couplings: High-speed rolling mill applications > 250 kW

3. INSPECTION CRITERIA
Spider Element (jaw coupling):
  - Replace if compression set > 15% of original thickness
  - Replace if cracks, chunking, or hardening visible
  - Service life: 12–18 months under normal conditions

Grid Element:
  - Replace if grid wear > 20% tooth depth
  - Regrease every 6 months (coupling grease NLGI-1)
  - Replace if hub bore shows fretting corrosion > 0.3 mm

4. ALIGNMENT PROCEDURE (CRITICAL — §4.3)
Angular misalignment check:
  - Use dial indicator on coupling OD, rotate 360°
  - Maximum TIR: 0.05 mm for speeds > 1,000 RPM; 0.10 mm for ≤ 1,000 RPM
Parallel misalignment check:
  - Straight-edge across both hub faces
  - Maximum offset: 0.05 mm per 100 mm of coupling diameter

If misalignment exceeds tolerance:
  - Adjust motor feet (shim to ±0.02 mm)
  - Re-check after tightening all hold-down bolts
  - Document final TIR in CMMS alignment record

5. REPLACEMENT PROCEDURE
- Follow LOTO per SOP-SAFETY-001 §3
- Heat hub to 80°C (induction heater) for removal/installation — no flame
- Torque hub retaining bolts per coupling manufacturer spec (see nameplate)
- Verify bore fit: H7/k6 interference for disc couplings

6. MAINTENANCE SCHEDULE
- Visual inspection: Monthly
- Alignment check with dial indicator: Quarterly and after any bearing replacement
- Full coupling replacement: Per condition or every 3 years
""",
        "category": "SOP",
        "equipment_type": "coupling",
        "fault_types": ["misalignment", "vibration", "wear"]
    },
    {
        "id": "SOP-ELECTRICAL-001",
        "title": "SOP: MV Motor Electrical Testing and Insulation Resistance Checks",
        "content": """
STANDARD OPERATING PROCEDURE – MV MOTOR ELECTRICAL MAINTENANCE
Document ID: SOP-ELECTRICAL-001 | Rev: 2.5 | Effective: 2024-01-20
Applicable Equipment: All 3.3 kV and 6.6 kV motors, Jamshedpur Plant

1. PURPOSE
Defines electrical testing procedures for medium-voltage motors to detect
winding degradation, insulation failure, and power quality issues.

2. INSULATION RESISTANCE (IR) TEST
Equipment: Megger 5 kV DC, calibrated within 12 months
Test Voltage Application:
  - 3.3 kV motors: Apply 2,500 VDC for 1 minute (PI test: 10 min)
  - 6.6 kV motors: Apply 5,000 VDC for 1 minute

Acceptance Criteria:
  - IR at 1 min: > 100 MΩ (minimum); > 1,000 MΩ (good condition)
  - Polarization Index (PI = IR10min / IR1min): > 2.0 (acceptable); > 4.0 (excellent)
  - PI < 1.5: Winding contamination — dry out required
  - PI < 1.0: Do NOT energise — rewind or replace

3. PARTIAL DISCHARGE (PD) TEST
- Perform offline PD test with 1.5× rated voltage for 10 minutes
- Acceptable: < 100 pC apparent charge
- Investigate: 100–500 pC with trend monitoring
- Replace: > 500 pC (imminent insulation failure)

4. MOTOR CURRENT SIGNATURE ANALYSIS (MCSA)
During normal operation, measure current spectrum via clip-on CT:
  - Broken rotor bar: Sidebands at (f ± 2sf) where s = slip, f = line frequency
  - Bearing fault: Sidebands at specific frequencies per bearing geometry
  - Eccentricity: Sidebands at (f ± nRPM/60) harmonics

5. THERMAL IMAGING
- Perform IR scan on motor terminal box at 75–100% load
  - ΔT < 10°C vs ambient: Normal
  - ΔT 10–25°C: Monitor, schedule inspection
  - ΔT > 25°C: Investigate loose connection or phase imbalance immediately

6. TEST FREQUENCY
- IR test (spot): Before commissioning and after any rewind
- IR test (trending): Annually for critical motors, biannually for others
- PD test: Every 3 years for motors > 5 years old
- Thermal imaging: Semi-annually
""",
        "category": "SOP",
        "equipment_type": "motor",
        "fault_types": ["insulation_failure", "winding_fault", "electrical_fault"]
    },
    {
        "id": "SOP-COOLANT-001",
        "title": "SOP: Coolant Water Quality Management – Blast Furnace Closed Circuit",
        "content": """
STANDARD OPERATING PROCEDURE – COOLANT WATER QUALITY
Document ID: SOP-COOLANT-001 | Rev: 3.3 | Effective: 2023-09-01
Applicable Equipment: BF-1 and BF-2 closed-circuit cooling systems, Jamshedpur

1. PURPOSE
Maintains cooling water chemistry to prevent corrosion, scaling, and biological
growth in blast furnace shell and stave cooling circuits.

2. TARGET WATER CHEMISTRY
Parameter          | Target Range     | Alarm Limit
pH                 | 7.5 – 9.0        | < 7.0 or > 9.5
Conductivity       | < 500 µS/cm      | > 800 µS/cm
Chlorides          | < 50 mg/L        | > 100 mg/L
Total Hardness     | < 200 mg/L CaCO₃ | > 300 mg/L
Turbidity          | < 5 NTU          | > 20 NTU
Total Bacteria     | < 100 CFU/mL     | > 1,000 CFU/mL

3. CHEMICAL DOSING
Corrosion inhibitor: Molybdate-based, maintain 100–150 ppm as MoO₄
Biocide: Non-oxidising type, dose 200 ppm bi-weekly
pH adjustment: Sodium hydroxide (NaOH) to raise pH; citric acid to lower
Scale inhibitor: Phosphonate blend, 20–30 ppm

4. BLOWDOWN CONTROL
- Maintain Cycles of Concentration (CoC) at 4–6
- Manual blowdown trigger: conductivity > 800 µS/cm
- Blowdown volume = (CoC – 1) × evaporation rate (approx. 1.5% of flow)
- Record all blowdown events in water treatment log WT-LOG

5. FAULT RESPONSE
Scaling (flow restriction, ΔP rise across heat exchanger):
  - Cause: Hardness above limit, insufficient scale inhibitor
  - Action: Circulate EDTA-based descaler at 2% for 4 hours, flush
  - Corrective: Increase softener regeneration frequency

Corrosion (reddish water, iron > 0.5 mg/L):
  - Cause: Low pH, depleted inhibitor, galvanic action
  - Action: Increase molybdate dose, adjust pH to 8.5
  - Corrective: Inspect vulnerable pipe sections with UT thickness gauge

Microbiological Fouling (slime, high bacteria count):
  - Cause: Inadequate biocide, warm stagnant zones
  - Action: Shock dose with oxidising biocide (chlorine 5 ppm for 2 hours)
  - Corrective: Flush dead-legs, install continuous dosing system

6. TESTING FREQUENCY
- pH, conductivity, turbidity: Daily (automated online monitors)
- Full chemistry panel: Weekly (lab analysis)
- Bacteria count: Weekly
- Corrosion coupon analysis: Quarterly
""",
        "category": "SOP",
        "equipment_type": "cooling_system",
        "fault_types": ["scaling", "corrosion", "fouling", "water_quality"]
    },
    {
        "id": "SOP-SENSOR-001",
        "title": "SOP: Condition Monitoring Sensor Calibration and Maintenance",
        "content": """
STANDARD OPERATING PROCEDURE – SENSOR CALIBRATION
Document ID: SOP-SENSOR-001 | Rev: 1.5 | Effective: 2024-04-01
Applicable Equipment: All online condition monitoring sensors, Jamshedpur Plant

1. PURPOSE
Ensures accuracy and reliability of vibration, temperature, pressure, and speed
sensors feeding the Stelos AI predictive maintenance system.

2. SENSOR TYPES AND CALIBRATION INTERVALS
Vibration (accelerometers, velocity probes):
  - Calibration: Annually using calibration shaker (NIST traceable)
  - Acceptance: ±5% of reference at 100 Hz, ±10% at 1 kHz
  - Replacement trigger: Sensitivity drift > 15% from factory spec

Temperature (RTD PT100, thermocouples):
  - Calibration: Semi-annually in temperature bath (0–200°C range)
  - Acceptance: ±0.5°C for RTDs; ±1.5°C for Type-K thermocouples
  - Replacement trigger: Drift > 3°C from reference at 100°C

Pressure Transmitters (4–20 mA):
  - Calibration: Semi-annually with dead-weight tester
  - Acceptance: ±0.25% of span
  - Zero/span adjustment: Via HART communicator, record in CMMS

Speed Sensors (proximity probes, encoders):
  - Calibration: Annually — compare against tachometer
  - Acceptance: ±0.5% of reading

3. CALIBRATION PROCEDURE (VIBRATION — EXAMPLE)
- Disconnect sensor from DCS/PLC (do not interrupt running machine)
- Mount calibration adaptor on sensor body
- Apply reference vibration (10 mm/s at 100 Hz)
- Record measured output vs reference
- Adjust sensitivity trim if within ±5%, replace if drift > 15%
- Issue calibration certificate, update CMMS calibration record

4. SENSOR HEALTH MONITORING
AI System flags:
  - Flat-line signal (< 0.001 V variation for > 5 min): Sensor fault
  - Signal spike (> 10× normal RMS, < 100 ms): Electrical interference
  - Drift pattern: Gradual upward/downward trend not matching process change

5. DATA QUALITY CHECKS (AUTOMATED)
- Stelos validates each sensor reading against ±3σ of 30-day baseline
- Flagged readings are excluded from ML model inference
- Sensor fault events logged to CMMS automatically via API

6. DOCUMENTATION
All calibration records stored in CMMS under Asset > Calibration > Sensor ID.
Retain certificates for 5 years per ISO 9001 requirement.
""",
        "category": "SOP",
        "equipment_type": "sensor",
        "fault_types": ["sensor_fault", "calibration_drift", "data_quality"]
    },
    {
        "id": "SOP-WELDING-001",
        "title": "SOP: Structural Weld Inspection – Conveyor Framework and Chutes",
        "content": """
STANDARD OPERATING PROCEDURE – STRUCTURAL WELD INSPECTION
Document ID: SOP-WELDING-001 | Rev: 2.0 | Effective: 2023-07-01
Applicable Equipment: Ore and coal conveyor structures, transfer chutes, Jamshedpur

1. PURPOSE
Defines visual and NDT inspection criteria for structural welds on conveyor
frameworks and transfer chutes subject to dynamic loading and abrasion.

2. INSPECTION TRIGGERS
- Planned: Semi-annual structural inspection per CMMS schedule
- Condition-based: Following impact events (belt slip, chute blockage clearing)
- After repair: Post-weld inspection before return to service

3. VISUAL INSPECTION CRITERIA
Reject if any of the following are present:
  - Cracks in weld bead or HAZ (heat-affected zone)
  - Undercut > 0.8 mm depth along weld toe
  - Porosity clusters > 3 pores per 25 mm of weld
  - Incomplete fusion visible at weld root (chute liner welds)
  - Distortion > 3 mm over 1 m span on primary load-bearing members

4. NDT METHODS
Magnetic Particle Inspection (MPI):
  - Use wet fluorescent method under UV light
  - Applicable to: all fillet welds on main conveyor frame beams
  - Rejection: Any linear indication > 2 mm length

Ultrasonic Testing (UT) — Thickness gauging:
  - Measure chute liner wear plates at grid points every 500 mm
  - Replacement: When thickness < 50% of original (typically < 6 mm for 12 mm plate)

Dye Penetrant (DP) for non-magnetic stainless sections:
  - Apply per ASTM E165 standard
  - Relevant indication: Any linear indication > 1.5 mm

5. REPAIR WELDING REQUIREMENTS
- Weld procedure specification (WPS) must be pre-qualified per AWS D1.1
- Welder qualification certificate required for structural welds
- Pre-heat carbon steel > 25 mm thickness to 100°C minimum
- Post-weld visual + MPI before painting or coating

6. DOCUMENTATION
- Complete inspection report on Form STRUCT-INSP-001
- Photograph all rejectable indications (reference measurement scale in photo)
- Upload to CMMS inspection record under Asset ID
""",
        "category": "SOP",
        "equipment_type": "structural",
        "fault_types": ["crack", "weld_failure", "structural_wear"]
    },
    {
        "id": "SOP-FILTER-001",
        "title": "SOP: Bag Filter and Dust Collection System Maintenance",
        "content": """
STANDARD OPERATING PROCEDURE – BAG FILTER MAINTENANCE
Document ID: SOP-FILTER-001 | Rev: 2.2 | Effective: 2024-01-10
Applicable Equipment: BF-FILTER-01 through BF-FILTER-06, Sinter Plant Dedusting

1. PURPOSE
Covers maintenance of pulse-jet bag filters used for dedusting at
sinter plant transfer points and blast furnace casthouse.

2. NORMAL OPERATING PARAMETERS
- Differential Pressure (ΔP): 800 – 1,800 Pa (alarm at 2,200 Pa)
- Air-to-Cloth Ratio: 1.2 – 1.8 m/min
- Pulse Cleaning Cycle: Every 30–120 s depending on ΔP
- Compressed Air for Cleaning: 4.5 – 6.0 bar
- Outlet Dust Concentration: < 20 mg/Nm³ (environmental limit)

3. FAULT RESPONSE
High ΔP (> 2,200 Pa):
  - Cause: Blinded bags, failed cleaning pulse valves, high inlet loading
  - Action: Verify pulse valve solenoids (listen for click at each cleaning cycle)
  - Corrective: Replace blinded bags (P/N BAG-PTFE-150), check compressed air supply

High Outlet Dust:
  - Cause: Torn bags, failed cage, bypass damper leak
  - Action: Visual inspection of outlet ductwork for dust deposition
  - Corrective: Isolate affected compartment, replace torn bags, inspect cage welds

Failed Pulse Valve:
  - Cause: Diaphragm failure, solenoid burn-out, moisture in air supply
  - Action: Isolate compartment, replace diaphragm kit (P/N PV-DIAP-85)
  - Preventive: Install air dryer/moisture separator on compressed air header

4. BAG REPLACEMENT PROCEDURE
- Isolate compartment (lock out inlet damper, verify ΔP = 0)
- PPE: Full face shield, P3 respirator, Tyvek suit (fine silica dust risk)
- Remove cage from top plate, extract old bag through top access
- Install new bag — ensure snap ring fully seated, no creases in lower section
- Replace cage without creasing bag, verify cage not touching bag at edges
- Run test cycle: verify ΔP < 1,500 Pa within 2 minutes of startup

5. MAINTENANCE SCHEDULE
- Differential pressure trending: Continuous (DCS alarm)
- Pulse valve check: Monthly (cycle test all valves)
- Bag inspection via access door: Quarterly
- Full bag replacement: Every 3–5 years or when outlet dust exceeds limit
- Air-to-cloth ratio calculation: Semi-annually (verify flow against design)
""",
        "category": "SOP",
        "equipment_type": "filter",
        "fault_types": ["high_pressure_drop", "bag_failure", "dust_emission"]
    },
    {
        "id": "FAR-2025-MILL-001",
        "title": "Failure Analysis Report: Rolling Mill Main Drive Gearbox Seizure – Jan 2025",
        "content": """
FAILURE ANALYSIS REPORT
Document ID: FAR-2025-MILL-001 | Date: 2025-01-28
Equipment: Hot Strip Mill Main Drive Gearbox (HSM-GBOX-02)
Reported by: Mechanical Maintenance Dept., Jamshedpur

INCIDENT SUMMARY
Catastrophic gearbox seizure on 2025-01-24 at 02:47 hrs during a scheduled night shift.
Equipment: 4-high reversing roughing mill, input shaft drive gearbox.
Downtime: 38 hours. Production loss: ~4,200 tonnes of semi-finished slabs.

FAILURE DESCRIPTION
Input shaft pinion (Z=18, module 14) suffered progressive pitting fatigue followed by
tooth fracture across 3 consecutive teeth. Fractured tooth fragment entered mesh,
caused scoring of the bull gear (Z=72), and locked the housing.

ROOT CAUSE ANALYSIS (5-WHY)
Why 1: Gearbox locked — tooth fracture caused binding.
Why 2: Tooth fractured — advanced contact fatigue (pitting) had reduced load-bearing section.
Why 3: Pitting progressed — lubrication film breakdown allowed metal-to-metal contact.
Why 4: Lubrication failed — oil viscosity had dropped from ISO VG 320 to VG 150
         (confirmed by oil sample taken 2 weeks before failure — not actioned).
Why 5: Low viscosity not actioned — oil sample result was logged but work order
         not raised; CMMS notification went to vacation-absent supervisor.

CONTRIBUTING FACTORS
- Oil change interval exceeded: last oil change 6,800 hours ago vs 5,000-hour SOP-GEARBOX-001 spec
- Vibration upward trend noted in Stelos AI 3 weeks prior (flagged WARNING, not CRITICAL)
- No metal particle count done on the flagged sample (only viscosity tested)

CORRECTIVE ACTIONS
1. Replace HSM-GBOX-02 complete gearbox unit (P/N GB-HSM-MAIN-02) — completed 2025-01-25
2. Mandatory: oil sample result triggers auto-work-order in CMMS (SAP workflow updated)
3. Inspection interval for gearboxes changed to 3,000 hours (from 5,000) for HSM drives
4. Metal particle count added to standard oil sample panel for all critical gearboxes
5. Stelos AI confidence threshold for gearbox WARNING reduced to trigger SMS alert

LESSONS LEARNED
Oil sample viscosity drop is a leading indicator for lubrication failure — act within 48 hours.
CMMS alerts must have backup contacts. Maintenance AI alerts need escalation workflow.
""",
        "category": "FAILURE_ANALYSIS",
        "equipment_type": "gearbox",
        "fault_types": ["gear_failure", "lubrication_failure", "seizure"]
    },
    {
        "id": "SOP-CRANE-001",
        "title": "SOP: Overhead Crane Hoist and Travel Mechanism Inspection",
        "content": """
STANDARD OPERATING PROCEDURE – OVERHEAD CRANE MAINTENANCE
Document ID: SOP-CRANE-001 | Rev: 3.1 | Effective: 2023-12-01
Applicable Equipment: EOT Cranes CR-01 through CR-18, Jamshedpur Shops

1. PURPOSE
Defines periodic inspection and maintenance for overhead electric overhead
travelling (EOT) cranes in steelmaking bays, material handling, and maintenance shops.

2. STATUTORY REQUIREMENTS
All EOT cranes are subject to Factories Act inspections:
  - Annual competency inspection by Certifying Engineer
  - Hydraulic overload test (125% SWL) every 5 years
  - Wire rope replacement based on discard criteria (IS 3973)

3. PRE-SHIFT CHECKS (OPERATOR)
- Test all limit switches: hoisting upper/lower, cross-travel end stops
- Verify hook latch closes fully and latch spring is intact
- Check brake action: apply full speed, trip power — crane must stop within 1 swing
- Verify festoon cable condition — no exposed wires, proper catenary sag

4. WEEKLY MAINTENANCE CHECKS
Hoist mechanism:
  - Inspect rope drum groove for uneven wear or rope crossovers
  - Measure rope diameter: reject if < 90% of nominal diameter (IS 3973 §6.3)
  - Check equaliser sheave bearing — grease weekly (NLGI-2 lithium)
  - Verify brake lining thickness: reject if < 3 mm remaining

Travel mechanism:
  - Check wheel flange wear: reject if flange thickness < 12 mm
  - Inspect rail clamps and festoon trolley rollers
  - Verify motor brake release gap: 0.3 – 0.5 mm (adjust per manufacturer)
  - Check gearbox oil level via dipstick

5. MONTHLY MAINTENANCE
- Lubricate all open gears (spray application, EP-1 grease)
- Megger test on hoist motor windings (> 50 MΩ acceptable)
- Check pendant cable insulation and pushbutton contacts
- Load test with calibrated test weight (SWL) — log results

6. WIRE ROPE DISCARD CRITERIA (IS 3973)
Discard rope if any of the following in any length of 8× rope diameter:
  - Broken wires: > 5% of total wire count in running ropes
  - Any broken wire in standing ropes or termination
  - Corrosion pitting visible on outer wires
  - Kinks, birdcaging, core protrusion, or crush damage
""",
        "category": "SOP",
        "equipment_type": "crane",
        "fault_types": ["rope_failure", "brake_failure", "mechanical_wear"]
    },
    {
        "id": "SOP-REFRACTORY-001",
        "title": "SOP: Refractory Lining Inspection – Blast Furnace Hearth and Taphole",
        "content": """
STANDARD OPERATING PROCEDURE – REFRACTORY INSPECTION
Document ID: SOP-REFRACTORY-001 | Rev: 4.0 | Effective: 2024-05-01
Applicable Equipment: BF-1 and BF-2 Blast Furnaces, Jamshedpur

1. PURPOSE
Defines inspection methods and response thresholds for blast furnace
refractory lining condition monitoring to prevent hearth breakout events.

2. MONITORING METHODS
Thermocouple Array (Primary):
  - 48 thermocouples embedded in BF hearth lining at 4 levels
  - Normal: 250–350°C at Level 1 (outermost ring)
  - Alert: > 450°C at Level 1 (lining thinning probable)
  - Critical: > 600°C or rate of rise > 20°C/day — consider controlled campaign end

Cooling Stave Heat Loss Monitoring:
  - Measure inlet/outlet cooling water ΔT across each stave circuit
  - Normal stave heat load: 8–12 kW per stave
  - Deteriorating stave: > 18 kW heat load (refractory protecting stave is worn)

Acoustic Emission:
  - Continuous monitoring for crack propagation events > 60 dB threshold

3. TAPHOLE CONDITION
- Taphole clay: Consume per campaign — check penetration depth after each cast
- Acceptance: Penetration depth 1.5 – 2.5 m on 4.5 m diameter hearth BF
- Deviation: < 1.5 m (underdrilling risk); > 3.0 m (lining erosion risk)
- Taphole drill and mud gun inspection: Per SOP-TAPHOLE-001

4. RESPONSE PROTOCOL
Level 1 Alert (thermocouple 450–550°C):
  - Increase cooling water flow by 20%
  - Apply titanium injection (TiO₂ via tuyeres) to build skull
  - Increase taphole mud volume by 10%
  - Schedule emergency inspection at next planned cast stop

Level 2 Critical (> 600°C or stave loss confirmed):
  - Reduce blast volume by 15%
  - Activate emergency water cooling (EWC) circuit
  - Initiate controlled shutdown sequence per SOP-SHUTDOWN-001
  - Convene emergency technical review within 4 hours

5. INSPECTION DURING PLANNED RELINES
- Measure lining profile by laser scanning and compare to design profile
- Sample spent refractory for porosity, density, and chemical analysis
- Document erosion patterns — correlate with operational data (Stelos AI)
- Update BF life model with actual wear rates for RUL prediction
""",
        "category": "SOP",
        "equipment_type": "blast_furnace",
        "fault_types": ["refractory_wear", "hearth_erosion", "taphole_failure"]
    },
    {
        "id": "SOP-LUBRICATION-002",
        "title": "SOP: Centralised Automatic Lubrication Systems – Conveyor Chains",
        "content": """
STANDARD OPERATING PROCEDURE – CENTRALISED LUBRICATION
Document ID: SOP-LUBRICATION-002 | Rev: 2.0 | Effective: 2024-02-01
Applicable Equipment: All chain conveyors with auto-lube systems, Jamshedpur

1. PURPOSE
Ensures correct setup and maintenance of centralised automatic lubrication
systems (Lincoln / SKF type) on heavy-duty chain conveyor drives.

2. SYSTEM COMPONENTS
- Central reservoir: 4–20 litre grease reservoir (NLGI-1 or NLGI-2)
- Pump unit: Electric or pneumatic, 60–150 bar output pressure
- Progressive divider valve (PDV) network: Distributes measured doses per lube point
- Piston distributors: Final delivery to each bearing/chain pin

3. NORMAL OPERATION
- Lube cycle interval: Set per equipment design — typically 15–60 min
- Dose per point: 0.05 – 0.5 mL per cycle (per lubrication plan)
- Reservoir refill alarm: At 20% remaining volume
- System pressure during cycle: 60–100 bar at pump output

4. FAULT DIAGNOSIS
No lubricant at bearing (starvation):
  - Check reservoir level — refill if low
  - Verify pump is cycling (listen for pump activation at set interval)
  - Check for PDV blockage — disconnect downstream of blocked divider, verify flow
  - Check for kinked or pinched tubing at lube point

High System Pressure (> 150 bar):
  - Cause: Blocked distributor, kinked line, frozen grease in cold weather
  - Action: Isolate affected zone, flush with thin oil, investigate blockage
  - Corrective: Replace seized piston distributor

System Not Cycling:
  - Check power supply to pump motor/solenoid
  - Verify timer/controller settings not reset after power interruption
  - Check pressure relief valve not stuck open

5. MAINTENANCE SCHEDULE
- Reservoir check and refill: Weekly
- PDV and distributor inspection: Monthly (verify movement of indicator pins)
- Full system flush and refill with fresh grease: Annually
- Tubing integrity inspection: Quarterly

6. GREASE SELECTION
- Standard: NLGI-2 lithium complex for temperatures –20°C to +130°C
- High temperature zones (> 100°C ambient): NLGI-1 calcium sulfonate complex
- Food-safe areas (if any): NSF H1 approved grease only
""",
        "category": "SOP",
        "equipment_type": "lubrication_system",
        "fault_types": ["lubrication_starvation", "blockage", "system_fault"]
    },
    {
        "id": "MAINT-BEST-PRACTICE-001",
        "title": "Best Practice Guide: RCM-Based Maintenance Strategy for Critical Rotating Equipment",
        "content": """
MAINTENANCE BEST PRACTICE GUIDE
Document ID: MAINT-BEST-PRACTICE-001 | Rev: 1.0 | Effective: 2024-06-01
Author: Tata Steel Reliability Engineering, Jamshedpur

1. RELIABILITY-CENTRED MAINTENANCE (RCM) PRINCIPLES
RCM is the framework used to determine maintenance strategies for critical assets.
It answers: What can go wrong? What happens if it does? What should be done to prevent it?

2. MAINTENANCE TASK SELECTION LOGIC
Condition-Based Maintenance (CBM — preferred for rotating equipment):
  - Applicable when: Detectable degradation precedes failure (P–F interval > 1 week)
  - Tools: Vibration analysis, oil analysis, thermal imaging, motor current signature
  - P–F interval for common failures:
    * Bearing fatigue: 2–8 weeks (vibration detectable)
    * Impeller wear: 4–12 weeks (flow/pressure degradable)
    * Insulation degradation: 6–18 months (IR test detectable)
    * Gear pitting: 4–16 weeks (oil metal particle detectable)

Time-Based Maintenance (TBM — for wear-out failure modes):
  - Applicable when: Failure rate increases with age (e.g., seals, filters, belts)
  - Set intervals at 50–60% of MTTR from failure history (conservative for critical assets)

Run-to-Failure (RTF — for non-critical, redundant items):
  - Applicable when: CBM not cost-effective, failure consequence is low, standby exists
  - Examples: Cooling fans with redundancy, instrument air filters, lighting

3. TATA STEEL CRITICALITY MATRIX (JAMSHEDPUR)
Critical (Red): Single-point, production-stopping, no standby → CBM + TBM (< 4-week intervals)
Major (Amber): Production impact > 1 hour, standby available → CBM (8-week intervals)
Minor (Green): No production impact or redundant → TBM or RTF

4. INTEGRATION WITH Stelos AI
Stelos AI output maps to this framework:
  - EMERGENCY → RTF failure in progress; execute emergency procedure immediately
  - CRITICAL → P–F interval likely < 1 week; execute CBM corrective action this shift
  - WARNING → P–F interval 1–4 weeks; schedule CBM within current maintenance window
  - NORMAL → Continue CBM monitoring at standard frequency

5. KPIs FOR MAINTENANCE EXCELLENCE
- OEE (Overall Equipment Effectiveness): Target > 87% for critical lines
- MTBF (Mean Time Between Failures): Track per equipment class; target ≥ 1.5× industry benchmark
- Maintenance Cost as % of RAV: Target < 2.5% (rotating equipment)
- PM Compliance: ≥ 95% of planned tasks on schedule
- Unplanned Downtime: < 2% of available production hours
""",
        "category": "BEST_PRACTICE",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
    {
        "id": "FAR-2025-PUMP-FAILURE",
        "title": "Failure Analysis Report: BF Cooling Pump Seal Failure – March 2025",
        "content": """
FAILURE ANALYSIS REPORT
Document ID: FAR-2025-PUMP-FAILURE | Date: 2025-03-15
Equipment: Blast Furnace Cooling Pump BF-Pump-11
Reported by: Process Maintenance, Jamshedpur

INCIDENT SUMMARY
BF-Pump-11 mechanical seal failed catastrophically on 2025-03-12, causing cooling
water loss to BF-1 north shell section. Emergency water switched to BF-Pump-10.
Downtime for repair: 6.5 hours. No furnace damage but blast reduction of 12% for 4 hours.

FAILURE DESCRIPTION
Double mechanical seal (inboard/outboard) failed at the inboard primary seal face.
Carbon seal face was cracked through in 3 places; mating silicon carbide face showed
concentric grooves from particulate abrasion.

ROOT CAUSE ANALYSIS
Primary: Particulate contamination in seal water supply caused abrasive wear of
carbon seal face at 3× normal rate. Estimated actual seal life: 4 months vs expected 18 months.

Contributing: Seal water filter cartridge (5 micron) had not been changed in 14 months
(SOP-PUMP-001 §4 specifies 6-month change). Filter was bypassed by operators during
a pressure excursion 2 months prior and not reinstated.

CORRECTIVE ACTIONS
1. Immediate: Replace seal assembly (P/N SEAL-MEC-BFP-11) with full cartridge seal unit
2. Seal water filter: Install 3-micron SS sintered element (non-bypassable design)
3. Bypass valve removed and blind flange installed on seal water filter bypass
4. Filter change added to CMMS PM task with 4-month interval (conservative)
5. Stelos AI: seal water pressure differential added as monitored parameter

FAILURE INDICATORS MISSED
- Seal water flow decrease of 15% noted in DCS trending for 3 weeks before failure
- Stelos vibration score had elevated over 2 weeks (0.42 → 0.68 mm/s RMS)
- No work order raised on either indicator

RECOMMENDATION
Seal water ΔP and vibration must both trigger CMMS work order automatically when
thresholds exceeded. Manual monitoring is insufficient for single-point cooling circuits.
""",
        "category": "FAILURE_ANALYSIS",
        "equipment_type": "pump",
        "fault_types": ["seal_failure", "contamination", "lubrication_failure"]
    },
    {
        "id": "SOP-PREDICTIVE-TOOLS-001",
        "title": "SOP: Using AI Predictive Maintenance Tools – Operator and Technician Guide",
        "content": """
STANDARD OPERATING PROCEDURE – AI PREDICTIVE MAINTENANCE TOOL USAGE
Document ID: SOP-PREDICTIVE-TOOLS-001 | Rev: 1.2 | Effective: 2025-01-01
Applicable: All maintenance technicians and operators, Jamshedpur Plant

1. PURPOSE
Guides operators and technicians on interpreting and acting on Stelos AI
predictive maintenance outputs to maximise equipment reliability.

2. UNDERSTANDING ALERT LEVELS
EMERGENCY (Red):
  - Meaning: ML model predicts failure within 0–24 hours (high confidence)
  - Required action: Notify shift supervisor immediately; prepare for controlled shutdown
  - Do NOT defer or dismiss without senior engineer approval and documented rationale

CRITICAL (Orange):
  - Meaning: Failure predicted within 1–7 days; significant degradation confirmed
  - Required action: Schedule corrective maintenance at next available window (≤ 48 hours)
  - Assign work order with parts pre-kitted before shift change

WARNING (Yellow):
  - Meaning: Early degradation detected; failure prediction 7–30 days
  - Required action: Increase monitoring frequency; plan maintenance for next shutdown
  - Document observation in shift logbook

NORMAL (Green):
  - Meaning: All parameters within acceptable bounds
  - Action: Continue standard monitoring schedule per SOP-SENSOR-001

3. INTERPRETING CONFIDENCE SCORES
- ≥ 0.85: High confidence — act on recommendation immediately
- 0.70 – 0.84: Moderate confidence — verify with physical inspection before acting
- 0.55 – 0.69: Low confidence — increased monitoring; request second opinion
- < 0.55: Very low — AI flagging anomaly but data may be noisy; check sensor calibration

4. ACTING ON RUL (REMAINING USEFUL LIFE) PREDICTIONS
RUL is given as days ± lower/upper bounds (Weibull model).
- Plan maintenance before the lower bound date for critical equipment
- For non-critical: maintenance before median RUL date is acceptable
- If RUL < 7 days and confidence > 0.75: treat as CRITICAL regardless of alert level shown

5. FEEDBACK TO IMPROVE AI ACCURACY
After completing maintenance:
  - Confirm the finding was accurate: use thumbs-up on AI Copilot
  - If AI was wrong (no defect found): thumbs-down and note actual condition
  - Note parts actually used: helps refine spare parts inventory recommendations
  - Feedback is automatically incorporated in model retraining (next 72-hour cycle)

6. ESCALATION CONTACTS
- Shift Supervisor: First point of contact for EMERGENCY alerts
- Reliability Engineer on call: For CRITICAL if maintenance not achievable in 48 hours
- OEM Technical Support: For novel failure modes with AI confidence < 0.60
""",
        "category": "SOP",
        "equipment_type": "all",
        "fault_types": ["all"]
    },
]


def get_all_documents():
    """Return all documents as list of (content_string, metadata) tuples for vector store."""
    docs = []
    for doc in KNOWLEDGE_DOCUMENTS:
        full_text = f"Title: {doc['title']}\n\n{doc['content']}"
        metadata = {
            "id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
            "equipment_type": doc["equipment_type"],
        }
        docs.append((full_text, metadata))
    return docs
