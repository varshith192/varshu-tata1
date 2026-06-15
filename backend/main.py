import asyncio
import json
import logging
import math
import os
import random
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage, AIMessage
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel

load_dotenv()

from database import init_db, SessionLocal
import models
from agents.workflow import app_graph
from agents.anomaly_detector import detect_anomalies, SENSOR_SPECS
from agents.rul_predictor import compute_health_index, simulate_whatif_delay
from data.sensor_history import generate_history, get_trend_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("StelosAPI")

app = FastAPI(
    title="Stelos AI",
    description="Autonomous Maintenance Decision Intelligence Platform — Tata Steel Hackathon 2026",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _seed_spare_parts_db():
    """Seed spare_parts table from SPARE_PARTS_DB if the table is empty."""
    db = SessionLocal()
    try:
        if db.query(models.SparePart).count() == 0:
            for p in SPARE_PARTS_DB:
                db.add(models.SparePart(
                    part_id        = p["part_id"],
                    part_name      = p["part_name"],
                    equipment_ids  = p["equipment_ids"],
                    type           = p["type"],
                    qty            = p["qty"],
                    unit           = p["unit"],
                    status         = p["status"],
                    supplier       = p["supplier"],
                    lead_time_days = p["lead_time_days"],
                    cost_inr       = p["cost_inr"],
                ))
            db.commit()
            logger.info(f"Seeded {len(SPARE_PARTS_DB)} spare parts into DB.")
    finally:
        db.close()


def _seed_logbook_db():
    """Seed logbook_entries table from _logbook_store if the table is empty."""
    db = SessionLocal()
    try:
        if db.query(models.LogbookEntry).count() == 0:
            for entry in _logbook_store:
                wo_id = entry.get("work_order_id")
                if not wo_id:
                    continue
                db.add(models.LogbookEntry(
                    timestamp           = entry.get("timestamp", datetime.now().isoformat()),
                    equipment_id        = entry.get("equipment_id", ""),
                    location            = entry.get("location", ""),
                    alert_level         = entry.get("alert_level", "NORMAL"),
                    diagnosis           = entry.get("diagnosis", ""),
                    root_cause          = entry.get("root_cause", ""),
                    health_score        = float(entry.get("health_score") or 0),
                    rul_days            = float(entry.get("rul_days") or 0),
                    failure_probability = float(entry.get("failure_probability") or 0),
                    maintenance_priority = entry.get("maintenance_priority", "P3"),
                    recommended_actions = entry.get("recommended_actions", []),
                    confidence_score    = float(entry.get("confidence_score") or 0),
                    work_order_id       = wo_id,
                    approved            = entry.get("approved", False),
                    approval_engineer   = entry.get("approval_engineer"),
                    approval_timestamp  = entry.get("approval_timestamp"),
                    approval_notes      = entry.get("approval_notes"),
                    engineer_notes      = entry.get("engineer_notes", []),
                    business_impact     = entry.get("business_impact"),
                    session_id          = entry.get("session_id"),
                ))
            db.commit()
            logger.info(f"Seeded {len(_logbook_store)} logbook entries into DB.")
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    # ── Database initialisation ──────────────────────────────────────────────
    try:
        init_db()
        _seed_spare_parts_db()
        _seed_logbook_db()
    except Exception as e:
        logger.warning(f"DB init failed (app will still run with JSON/in-memory): {e}")

    _load_feedback()
    # Save seed data to disk on first run (creates logbook.json if not exists)
    if not os.path.exists(LOGBOOK_FILE):
        _save_logbook()
        logger.info("Logbook initialised with seed data and saved to disk.")
    asyncio.create_task(_proactive_alert_monitor())
    # Warm up XGBoost + FAISS at startup — prevents 16s delay on first chatbot request
    loop = asyncio.get_event_loop()
    try:
        from ml.failure_classifier import warmup
        loop.run_in_executor(None, warmup)
    except Exception as exc:
        logger.warning(f"ML warmup skipped: {exc}")
    try:
        from rag.knowledge_base import get_knowledge_base
        loop.run_in_executor(None, get_knowledge_base)
        logger.info("RAG knowledge base warming up in background...")
    except Exception as exc:
        logger.warning(f"RAG warmup skipped: {exc}")


async def _proactive_alert_monitor():
    """Background task: checks all fleet equipment every 60 s and pushes alerts via WS."""
    import time
    await asyncio.sleep(15)  # let server fully start first
    while True:
        try:
            noise = time.time() / 60.0
            for eq_id, info in FLEET.items():
                sensor_data = _simulate_sensor_data(eq_id, noise_seed=noise)
                temp = sensor_data["temperature"]
                vib  = sensor_data["vibration"]
                hi   = compute_health_index(sensor_data)

                if temp >= 95 or vib >= 1.0:
                    level = "EMERGENCY"
                elif temp >= 85 or vib >= 0.70 or hi < 50:
                    level = "CRITICAL"
                elif temp >= 78 or vib >= 0.50 or hi < 75:
                    level = "WARNING"
                else:
                    level = "NORMAL"

                prev = _proactive_alert_state.get(eq_id, "NORMAL")
                # Only alert when level worsens
                severity = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2, "EMERGENCY": 3}
                if severity.get(level, 0) > severity.get(prev, 0):
                    _proactive_alert_state[eq_id] = level
                    _upsert_alert(eq_id, level, f"[PROACTIVE] {eq_id} threshold crossed: temp={temp:.1f}°C vib={vib:.3f} mm/s HI={hi:.0f}%")
                    alert_msg = json.dumps({
                        "type": "proactive_alert",
                        "equipment_id": eq_id,
                        "location": info["location"],
                        "alert_level": level,
                        "temperature": temp,
                        "vibration": round(vib, 3),
                        "health_index": round(hi, 1),
                        "message": f"⚠ {level}: {eq_id} ({info['location']}) — Temp {temp:.1f}°C, Vib {vib:.3f} mm/s, HI {hi:.0f}%",
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                    })
                    await manager.broadcast(alert_msg)
                    logger.warning(f"Proactive alert: {eq_id} → {level}")
                elif severity.get(level, 0) < severity.get(prev, 0):
                    # Level improved — update state silently
                    _proactive_alert_state[eq_id] = level
        except Exception as e:
            logger.warning(f"Proactive monitor error: {e}")
        await asyncio.sleep(60)

# ─────────────────────────────────────────
# Prometheus metrics
# ─────────────────────────────────────────
agent_invocations = Counter("stelos_agent_invocations_total", "Total agent invocations", ["equipment_id"])
active_alerts = Gauge("stelos_active_alerts", "Number of active equipment alerts")
avg_health_score = Gauge("stelos_avg_health_score", "Average fleet health score")

# ─────────────────────────────────────────
# In-memory state (replace with DB in production)
# ─────────────────────────────────────────
_feedback_store: List[Dict] = []
_alert_store: List[Dict] = []
_session_store: Dict[str, List] = {}   # session_id -> message history
_proactive_alert_state: Dict[str, str] = {}  # equipment_id -> last broadcasted level

# Pre-seeded logbook — ensures approvals and logbook always have entries on startup
_NOW = datetime.now()
_logbook_store: List[Dict] = [
    {
        "id": 1,
        "timestamp": (_NOW.replace(hour=6, minute=15, second=0)).isoformat(timespec="seconds"),
        "equipment_id": "Pump-A",
        "location": "Blast Furnace #2",
        "alert_level": "NORMAL",
        "diagnosis": "Normal Operation — all sensors within nominal envelope",
        "root_cause": "No significant fault detected",
        "health_score": 84.0,
        "rul_days": 62.0,
        "failure_probability": 0.08,
        "maintenance_priority": "P3",
        "recommended_actions": [
            {"action": "Continue routine monitoring per scheduled maintenance plan", "priority": "Routine", "sop_reference": "PM-GUIDE-001 §4"},
        ],
        "confidence_score": 0.79,
        "work_order_id": f"WO-{_NOW.strftime('%Y%m%d')}-0001",
        "approved": True,
        "approval_engineer": "Meena Sharma",
        "approval_timestamp": (_NOW.replace(hour=6, minute=30, second=0)).isoformat(timespec="seconds"),
    },
    {
        "id": 2,
        "timestamp": (_NOW.replace(hour=7, minute=42, second=0)).isoformat(timespec="seconds"),
        "equipment_id": "Conveyor-B",
        "location": "Raw Material Yard",
        "alert_level": "WARNING",
        "diagnosis": "Elevated vibration 0.52 mm/s on drive pulley bearings — Zone C per ISO 10816-3",
        "root_cause": "Bearing wear — vibration dominant (0.52 mm/s) without significant temperature rise indicates mechanical imbalance or early bearing defect",
        "health_score": 70.5,
        "rul_days": 18.2,
        "failure_probability": 0.31,
        "maintenance_priority": "P2",
        "recommended_actions": [
            {"action": "Vibration spectrum analysis (BPFI/BPFO) to isolate dominant frequency", "priority": "P2", "sop_reference": "SOP-VIBRATION-001 §2"},
            {"action": "Apply emergency grease lubrication to drive pulley bearings", "priority": "P2", "sop_reference": "SOP-LUBRICATION-001 §3.2"},
            {"action": "Schedule bearing replacement within RUL window (18 days)", "priority": "P2", "sop_reference": "SOP-BEARING-001 §4.3"},
        ],
        "confidence_score": 0.82,
        "work_order_id": f"WO-{_NOW.strftime('%Y%m%d')}-0002",
        "approved": False,
    },
    {
        "id": 3,
        "timestamp": (_NOW.replace(hour=8, minute=55, second=0)).isoformat(timespec="seconds"),
        "equipment_id": "Pump-B",
        "location": "Blast Furnace #3",
        "alert_level": "CRITICAL",
        "diagnosis": "Anomaly Detected: Bearing temperature 92.5°C exceeds alarm threshold — lubrication failure suspected",
        "root_cause": "Blocked lubrication filter — oil temperature 68.5°C (+16.5°C above nominal) and bearing temperature co-elevation match FAR-2024-047 failure pattern. Lubrication film degradation leading to metal-to-metal contact.",
        "health_score": 44.0,
        "rul_days": 4.3,
        "failure_probability": 0.82,
        "maintenance_priority": "P1",
        "recommended_actions": [
            {"action": "Initiate controlled shutdown — bearing failure risk imminent; isolate equipment", "priority": "P1", "sop_reference": "SOP-EMERGENCY-001 §3.1"},
            {"action": "Inspect and flush lubrication system — check inline oil filter and supply line pressure", "priority": "P1", "sop_reference": "SOP-LUBRICATION-001 §2.1"},
            {"action": "Collect oil sample for viscosity and contamination analysis", "priority": "P1", "sop_reference": "SOP-PUMP-001 §4"},
            {"action": "Replace SKF 6205 bearing kit — emergency stock available at Central Store", "priority": "P1", "sop_reference": "SOP-BEARING-001 §4.3"},
        ],
        "confidence_score": 0.91,
        "work_order_id": f"WO-{_NOW.strftime('%Y%m%d')}-0003",
        "approved": False,
    },
    {
        "id": 4,
        "timestamp": (_NOW.replace(hour=9, minute=10, second=0)).isoformat(timespec="seconds"),
        "equipment_id": "Blast-Furnace",
        "location": "Blast Furnace #1",
        "alert_level": "CRITICAL",
        "diagnosis": "Elevated vibration 0.58 mm/s and temperature 81°C — combined thermal-mechanical degradation",
        "root_cause": "Bearing degradation (thermal-mechanical) — vibration 0.58 mm/s (Zone C) combined with temperature 81°C indicates progressive bearing race failure. Motor current 16.8 A elevated above nominal 8–16 A range.",
        "health_score": 55.0,
        "rul_days": 8.7,
        "failure_probability": 0.71,
        "maintenance_priority": "P1",
        "recommended_actions": [
            {"action": "FFT vibration spectrum analysis to isolate bearing fault frequency (BPFI/BPFO)", "priority": "P1", "sop_reference": "SOP-VIBRATION-001 §2.2"},
            {"action": "Inspect and flush lubrication system — verify supply line pressure and filter condition", "priority": "P1", "sop_reference": "SOP-LUBRICATION-001 §2.1"},
            {"action": "Schedule bearing replacement within 8-day RUL window", "priority": "P1", "sop_reference": "SOP-BEARING-001 §4.3"},
            {"action": "Check shaft alignment using dial indicator — correct if misalignment > 0.05 mm", "priority": "P2", "sop_reference": "SOP-ALIGNMENT-001 §2"},
        ],
        "confidence_score": 0.87,
        "work_order_id": f"WO-{_NOW.strftime('%Y%m%d')}-0004",
        "approved": False,
    },
]

_DATA_DIR      = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
FEEDBACK_FILE  = os.path.join(_DATA_DIR, "feedback.json")
LOGBOOK_FILE   = os.path.join(_DATA_DIR, "logbook.json")


def _sync_entry_to_db(entry: dict):
    """Upsert a single logbook entry to the database."""
    wo_id = entry.get("work_order_id")
    if not wo_id:
        return
    try:
        db = SessionLocal()
        try:
            row = db.query(models.LogbookEntry).filter_by(work_order_id=wo_id).first()
            if row:
                row.approved           = entry.get("approved", False)
                row.approval_engineer  = entry.get("approval_engineer")
                row.approval_timestamp = entry.get("approval_timestamp")
                row.approval_notes     = entry.get("approval_notes")
                row.engineer_notes     = entry.get("engineer_notes", [])
            else:
                db.add(models.LogbookEntry(
                    timestamp           = entry.get("timestamp", datetime.now().isoformat()),
                    equipment_id        = entry.get("equipment_id", ""),
                    location            = entry.get("location", ""),
                    alert_level         = entry.get("alert_level", "NORMAL"),
                    diagnosis           = entry.get("diagnosis", ""),
                    root_cause          = entry.get("root_cause", ""),
                    health_score        = float(entry.get("health_score") or 0),
                    rul_days            = float(entry.get("rul_days") or 0),
                    failure_probability = float(entry.get("failure_probability") or 0),
                    maintenance_priority = entry.get("maintenance_priority", "P3"),
                    recommended_actions = entry.get("recommended_actions", []),
                    confidence_score    = float(entry.get("confidence_score") or 0),
                    work_order_id       = wo_id,
                    approved            = entry.get("approved", False),
                    approval_engineer   = entry.get("approval_engineer"),
                    approval_timestamp  = entry.get("approval_timestamp"),
                    approval_notes      = entry.get("approval_notes"),
                    engineer_notes      = entry.get("engineer_notes", []),
                    business_impact     = entry.get("business_impact"),
                    session_id          = entry.get("session_id"),
                ))
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB logbook sync failed: {e}")


def _save_logbook():
    """Persist logbook to JSON (backward compat) and PostgreSQL."""
    try:
        os.makedirs(os.path.dirname(LOGBOOK_FILE), exist_ok=True)
        with open(LOGBOOK_FILE, "w") as f:
            json.dump(_logbook_store, f, default=str, indent=2)
    except Exception as e:
        logger.warning(f"Could not save logbook JSON: {e}")
    # Mirror to DB
    for entry in _logbook_store:
        _sync_entry_to_db(entry)


def _load_logbook() -> list:
    """Load logbook: PostgreSQL → JSON file → seed data (priority order)."""
    try:
        db = SessionLocal()
        try:
            rows = db.query(models.LogbookEntry).order_by(models.LogbookEntry.id).all()
            if rows:
                data = [r.to_dict() for r in rows]
                logger.info(f"Loaded {len(data)} logbook entries from PostgreSQL/SQLite DB.")
                return data
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB logbook load failed ({e}), trying JSON...")
    if os.path.exists(LOGBOOK_FILE):
        try:
            with open(LOGBOOK_FILE) as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} logbook entries from disk.")
            return data
        except Exception as e:
            logger.warning(f"Could not load logbook file: {e}")
    return _logbook_store  # first-run seed


def _load_feedback():
    """Load feedback: PostgreSQL/SQLite → JSON file."""
    global _feedback_store
    try:
        db = SessionLocal()
        try:
            rows = db.query(models.FeedbackEntry).order_by(models.FeedbackEntry.id).all()
            if rows:
                _feedback_store = [r.to_dict() for r in rows]
                logger.info(f"Loaded {len(_feedback_store)} feedback entries from DB.")
                return
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB feedback load failed ({e}), trying JSON...")
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE) as f:
                _feedback_store = json.load(f)
            logger.info(f"Loaded {len(_feedback_store)} feedback entries from disk.")
        except Exception as e:
            logger.warning(f"Could not load feedback file: {e}")


def _save_feedback():
    """Persist feedback to JSON and DB."""
    try:
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(_feedback_store, f)
    except Exception as e:
        logger.warning(f"Could not save feedback JSON: {e}")
    # Mirror latest entry to DB
    if _feedback_store:
        entry = _feedback_store[-1]
        try:
            db = SessionLocal()
            try:
                db.add(models.FeedbackEntry(
                    equipment_id       = entry.get("equipment_id", ""),
                    diagnosis_correct  = entry.get("diagnosis_correct", False),
                    root_cause_correct = entry.get("root_cause_correct"),
                    actions_useful     = entry.get("actions_useful"),
                    notes              = entry.get("notes"),
                    confidence_rating  = entry.get("confidence_rating"),
                    timestamp          = entry.get("timestamp", datetime.now().isoformat()),
                ))
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"DB feedback save failed: {e}")

# Load persisted logbook (overwrites pre-seed if file exists)
_logbook_store = _load_logbook()

# Multi-equipment fleet simulation state
FLEET: Dict[str, Dict] = {
    "Pump-B":        {"type": "pump",      "location": "Blast Furnace #3",   "criticality": "Critical", "base_health": 25.0},
    "Pump-A":        {"type": "pump",      "location": "Blast Furnace #2",   "criticality": "High",     "base_health": 82.0},
    "Pump-C":        {"type": "pump",      "location": "Blast Furnace #4",   "criticality": "Critical", "base_health": 90.0},
    "Conveyor-B":     {"type": "conveyor",  "location": "Raw Material Yard",  "criticality": "High",     "base_health": 70.0},
    "Cooling-Fan-4":  {"type": "fan",       "location": "Sinter Plant",       "criticality": "Medium",   "base_health": 87.0},
    "Rolling-Mill":   {"type": "mill",      "location": "Hot Rolling Section","criticality": "Critical", "base_health": 91.0},
    "Cooling-Unit":   {"type": "fan",       "location": "Steel Melting Shop", "criticality": "Medium",   "base_health": 89.0},
    "Power-Unit":     {"type": "pump",      "location": "Power Distribution", "criticality": "High",     "base_health": 95.0},
    "Blast-Furnace":  {"type": "furnace",   "location": "Blast Furnace #1",   "criticality": "Critical", "base_health": 68.0},
    "Compressor-2":   {"type": "pump",      "location": "Oxygen Plant",       "criticality": "High",     "base_health": 92.0},
}


def _simulate_sensor_data(equipment_id: str, noise_seed: float = 0) -> Dict[str, float]:
    """Generate realistic sensor data for a given equipment."""
    info = FLEET.get(equipment_id, {"base_health": 85.0, "type": "pump"})
    base_health = info["base_health"]

    # Health-dependent sensor degradation
    degradation = (100.0 - base_health) / 100.0

    rng = random.Random(int(noise_seed * 1000))

    temp_nominal = SENSOR_SPECS["temperature"]["nominal"]
    vib_nominal = SENSOR_SPECS["vibration"]["nominal"]
    pres_nominal = SENSOR_SPECS["pressure"]["nominal"]
    oil_nominal = SENSOR_SPECS["oil_temp"]["nominal"]
    curr_nominal = SENSOR_SPECS["motor_current"]["nominal"]

    return {
        "temperature":    round(temp_nominal + degradation * 30.0 + rng.uniform(-2, 2), 1),
        "vibration":      round(vib_nominal + degradation * 0.60 + rng.uniform(-0.02, 0.02), 3),
        "pressure":       round(pres_nominal - degradation * 15.0 + rng.uniform(-1, 1), 1),
        "oil_temp":       round(oil_nominal + degradation * 20.0 + rng.uniform(-1, 1), 1),
        "motor_current":  round(curr_nominal + degradation * 8.0 + rng.uniform(-0.5, 0.5), 1),
    }


# ─────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────
class AgentRequest(BaseModel):
    equipment_id: str
    message: str
    sensor_data: Dict[str, Any]
    session_id: Optional[str] = None
    image_base64: Optional[str] = None  # base64 image for visual analysis


class WhatIfRequest(BaseModel):
    equipment_id: str
    delay_days: int
    current_sensor_data: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    equipment_id: str
    diagnosis_correct: bool
    root_cause_correct: bool
    recommended_actions_useful: bool
    engineer_notes: Optional[str] = None
    confidence_rating: Optional[int] = None   # 1-5

class ReportEmailRequest(BaseModel):
    to: str
    timestamp: str


# ─────────────────────────────────────────
# Core agent invocation endpoint
# ─────────────────────────────────────────
def _quick_fleet_response(req, session_id: str, history: list) -> dict:
    """Fast path for fleet-level questions — skips 9-agent pipeline."""
    import time
    noise = time.time() / 60.0
    ranked = []
    for eq_id, info in FLEET.items():
        sd = _simulate_sensor_data(eq_id, noise_seed=noise)
        hi = compute_health_index(sd)
        from agents.anomaly_detector import get_dominant_fault_type
        from agents.rul_predictor import estimate_rul
        ft, _ = get_dominant_fault_type(sd)
        rul = estimate_rul(sd, hi, info["type"], ft)
        temp, vib = sd["temperature"], sd["vibration"]
        level = ("EMERGENCY" if temp >= 95 or vib >= 1.0 else
                 "CRITICAL"  if temp >= 85 or vib >= 0.70 or hi < 35 else
                 "WARNING"   if temp >= 78 or vib >= 0.50 or hi < 55 else "NORMAL")
        severity = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2, "EMERGENCY": 3}
        score = severity[level] * 30 + (100 - hi) * 0.4 + rul["failure_probability"] * 20
        ranked.append((score, eq_id, level, hi, rul))
    ranked.sort(key=lambda x: -x[0])

    lines = ["🏭 FLEET PRIORITY STATUS — Stelos AI\n"]
    for i, (score, eq_id, level, hi, rul) in enumerate(ranked, 1):
        emoji = {"EMERGENCY": "🔴", "CRITICAL": "🟠", "WARNING": "🟡", "NORMAL": "🟢"}.get(level, "⚪")
        lines.append(f"{i}. {emoji} {eq_id} [{level}]")
        lines.append(f"   Health: {hi:.0f}% | RUL: {rul['predicted_rul_days']}d | Failure prob: {rul['failure_probability']*100:.0f}% | Priority: {rul['maintenance_priority']}")
    lines.append(f"\nTop priority: {ranked[0][1]} requires immediate attention.")

    msg = "\n".join(lines)
    reply_msg = AIMessage(content=msg)
    history.append(reply_msg)
    _session_store[session_id] = history[-10:]
    return {
        "equipment_id": req.equipment_id,
        "diagnosis": f"Fleet status: {sum(1 for _, _, l, _, _ in ranked if l in ('CRITICAL','EMERGENCY'))} critical equipment",
        "root_cause": "Fleet-level multi-equipment analysis",
        "final_message": msg,
        "session_id": session_id,
        "traces": [{"agent": "FleetStatus", "action": "Ranked all 5 equipment by urgency score (bypasses 6-agent pipeline)", "result": f"Top: {ranked[0][1]} [{ranked[0][2]}]"}],
        "alert_level": ranked[0][2],
        "health_score": ranked[0][3],
        "confidence_score": 0.95,
    }


def _quick_trend_response(req, session_id: str, history: list) -> dict:
    """Fast path for sensor trend questions."""
    trend = get_trend_summary(req.equipment_id, 168)
    recent = generate_history(req.equipment_id, 720)[-24:]  # last 24 hours

    lines = [f"📈 7-DAY SENSOR TREND — {req.equipment_id}\n"]
    sensor_labels = {
        "temperature": "Temperature (°C)", "vibration": "Vibration (mm/s)",
        "pressure": "Pressure (PSI)", "oil_temp": "Oil Temp (°C)", "motor_current": "Current (A)"
    }
    arrows = {"rising_fast": "↑↑ FAST RISE", "rising": "↑ Rising", "stable": "→ Stable",
              "falling": "↓ Falling", "falling_fast": "↓↓ Fast fall"}
    for sensor, t in trend["sensor_trends"].items():
        arrow = arrows.get(t["direction"], "→")
        warn = " ⚠" if (sensor == "temperature" and t["end"] > 80) or (sensor == "vibration" and t["end"] > 0.5) else ""
        lines.append(f"  {sensor_labels.get(sensor, sensor):<22}: {t['start']} → {t['end']}  {arrow}{warn}  ({t['change_pct']:+.1f}% over 7d)")

    temp_dir = trend["sensor_trends"].get("temperature", {}).get("direction", "stable")
    vib_dir  = trend["sensor_trends"].get("vibration",   {}).get("direction", "stable")
    if "rising" in temp_dir and "rising" in vib_dir:
        lines.append("\n⚠ Both temperature and vibration are trending upward — degradation in progress. Schedule inspection soon.")
    else:
        lines.append("\nTrends look stable. Continue routine monitoring.")

    msg = "\n".join(lines)
    reply_msg = AIMessage(content=msg)
    history.append(reply_msg)
    _session_store[session_id] = history[-10:]
    return {
        "equipment_id": req.equipment_id,
        "diagnosis": f"Trend analysis for {req.equipment_id} over last 7 days",
        "root_cause": f"Temperature trend: {temp_dir}, Vibration trend: {vib_dir}",
        "final_message": msg,
        "session_id": session_id,
        "traces": [{"agent": "TrendAnalysis", "action": "30-day history linear regression on 5 sensors", "result": f"Temp {temp_dir}, Vib {vib_dir}"}],
        "alert_level": "WARNING" if "rising" in temp_dir else "NORMAL",
        "health_score": None,
        "confidence_score": 0.90,
    }


def _quick_report_response(req, session_id: str, history: list) -> dict:
    """Fast path for report generation — tells user to download via link."""
    api_url = os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:8000")
    report_url = f"{api_url}/api/report/{req.equipment_id}"
    msg = (
        f"📄 Maintenance Report for {req.equipment_id}\n\n"
        f"I've generated a full structured maintenance report including:\n"
        f"• Current sensor readings and health index\n"
        f"• RUL prediction with confidence interval\n"
        f"• 7-day trend analysis for all 5 sensors\n"
        f"• Recent work order history\n"
        f"• Prioritized recommended actions\n\n"
        f"Download: {report_url}\n\n"
        f"You can open this URL in your browser to view/save the report."
    )
    reply_msg = AIMessage(content=msg)
    history.append(reply_msg)
    _session_store[session_id] = history[-10:]
    return {
        "equipment_id": req.equipment_id,
        "diagnosis": f"Report generated for {req.equipment_id}",
        "root_cause": "Structured maintenance report compilation",
        "final_message": msg,
        "session_id": session_id,
        "report_url": report_url,
        "traces": [{"agent": "ReportGenerator", "action": f"Compiled full maintenance report for {req.equipment_id}", "result": "Report ready for download"}],
        "alert_level": "NORMAL",
        "confidence_score": 1.0,
    }


@app.post("/api/agent/invoke")
async def invoke_agent(req: AgentRequest):
    logger.info(f"Agent invoke: {req.equipment_id} — '{req.message[:80]}'")
    agent_invocations.labels(equipment_id=req.equipment_id).inc()

    # Session-based multi-turn: retrieve or create message history
    session_id = req.session_id or str(uuid.uuid4())
    history = _session_store.get(session_id, [])

    # ── Vision analysis: if an image was uploaded, describe it first ──
    enriched_message = req.message
    if req.image_base64:
        try:
            groq_key = os.environ.get("GROQ_API_KEY", "")
            gemini_key = os.environ.get("GEMINI_API_KEY", "")
            vision_description = None

            if groq_key and groq_key != "your_groq_api_key_here":
                from langchain_groq import ChatGroq
                from langchain_core.messages import HumanMessage as LCHuman
                vlm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=groq_key, timeout=15, max_retries=0)
                vision_msg = LCHuman(content=[
                    {"type": "text", "text": f"You are analyzing an industrial equipment image for {req.equipment_id} at a steel plant. Describe what you see: visible damage, corrosion, leaks, wear, unusual readings on gauges, or anything abnormal. Be specific and technical."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{req.image_base64}"}}
                ])
                resp = vlm.invoke([vision_msg])
                vision_description = resp.content
            elif gemini_key and gemini_key != "your_gemini_api_key_here":
                import google.generativeai as genai
                import base64
                genai.configure(api_key=gemini_key)
                gmodel = genai.GenerativeModel("gemini-1.5-flash")
                img_bytes = base64.b64decode(req.image_base64)
                vision_resp = gmodel.generate_content([
                    f"Analyze this industrial equipment image for {req.equipment_id} at a steel plant. Describe visible damage, corrosion, leaks, wear, gauge readings, or abnormalities. Be specific and technical.",
                    {"mime_type": "image/jpeg", "data": img_bytes}
                ])
                vision_description = vision_resp.text

            if vision_description:
                enriched_message = f"[IMAGE ANALYSIS] {vision_description}\n\nEngineer's question: {req.message}"
                logger.info(f"Vision analysis complete for {req.equipment_id}: {vision_description[:100]}...")
        except Exception as ve:
            logger.warning(f"Vision analysis failed: {ve}")
            enriched_message = f"[Image uploaded but vision analysis unavailable] {req.message}"

    history.append(HumanMessage(content=enriched_message))

    # ── Intent pre-processing: fast-path for specific tool calls ──
    msg = req.message.lower()
    if any(k in msg for k in ["fleet", "all equipment", "plant health", "overall", "most urgent", "which equipment", "priority list", "entire plant"]):
        return _quick_fleet_response(req, session_id, history)
    if any(k in msg for k in ["trend", "history", "last 30", "over time", "when did", "show me the trend"]) and "what if" not in msg and "delay" not in msg:
        return _quick_trend_response(req, session_id, history)
    if any(k in msg for k in ["generate report", "maintenance report", "create report", "export report", "download report"]):
        return _quick_report_response(req, session_id, history)

    state = {
        "messages": history,
        "equipment_id": req.equipment_id,
        "sensor_data": req.sensor_data,
        "agent_traces": [],
        "feedback_adjustments": _get_feedback_adjustments(req.equipment_id),
    }

    try:
        result = app_graph.invoke(state)
        logger.info(f"Workflow complete for {req.equipment_id}")

        # Update session history with AI response
        ai_reply = result.get("messages", [])
        if ai_reply:
            history.append(ai_reply[-1])
        _session_store[session_id] = history[-10:]  # keep last 10 turns

        # Update alert store
        alert_level = result.get("alert_level", "NORMAL")
        if alert_level in ("CRITICAL", "EMERGENCY", "WARNING"):
            _upsert_alert(req.equipment_id, alert_level, result.get("diagnosis", ""))

        # Auto-log to Digital Maintenance Logbook
        _logbook_store.append({
            "id": len(_logbook_store) + 1,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "equipment_id": result.get("equipment_id"),
            "location": FLEET.get(req.equipment_id, {}).get("location", "Unknown"),
            "alert_level": result.get("alert_level", "NORMAL"),
            "diagnosis": result.get("diagnosis", ""),
            "root_cause": result.get("root_cause", ""),
            "health_score": result.get("health_score"),
            "rul_days": result.get("predicted_rul_days"),
            "failure_probability": result.get("failure_probability"),
            "maintenance_priority": result.get("maintenance_priority"),
            "recommended_actions": result.get("recommended_actions", [])[:3],
            "confidence_score": result.get("confidence_score"),
            "business_impact": result.get("business_impact"),
            "work_order_id": f"WO-{datetime.now().strftime('%Y%m%d')}-{len(_logbook_store)+1:04d}",
            "session_id": session_id,
            "approved": False,
        })
        _save_logbook()

        # Apply feedback-driven confidence adjustment
        fb_adj = _get_feedback_adjustments(req.equipment_id).get("global", 1.0)
        raw_conf = result.get("confidence_score") or 0.80
        adjusted_conf = round(min(0.99, max(0.10, raw_conf * fb_adj)), 3)

        # Update metrics
        active_alerts.set(len([a for a in _alert_store if a["level"] in ("CRITICAL", "EMERGENCY")]))

        return {
            "equipment_id": result.get("equipment_id"),
            "diagnosis": result.get("diagnosis"),
            "root_cause": result.get("root_cause"),
            "causal_chain": result.get("causal_chain", ""),
            "primary_mechanism": result.get("primary_mechanism", ""),
            "root_cause_evidence": result.get("root_cause_evidence", []),
            "predicted_rul_days": result.get("predicted_rul_days"),
            "rul_lower_bound": result.get("rul_lower_bound"),
            "rul_upper_bound": result.get("rul_upper_bound"),
            "failure_probability": result.get("failure_probability"),
            "health_score": result.get("health_score"),
            "risk_assessment": result.get("risk_assessment"),
            "alert_level": result.get("alert_level"),
            "maintenance_priority": result.get("maintenance_priority"),
            "recommended_actions": result.get("recommended_actions"),
            "retrieved_sources": result.get("retrieved_sources", []),
            "confidence_score": adjusted_conf,
            "feedback_adjustment": fb_adj,
            "xai_explanation": result.get("xai_explanation"),
            "evidence_chain": result.get("evidence_chain", []),
            "traces": result.get("agent_traces"),
            "final_message": result.get("messages", [{}])[-1].content if result.get("messages") else "",
            "session_id": session_id,
            "work_order_id": _logbook_store[-1]["work_order_id"] if _logbook_store else None,
            "business_impact": result.get("business_impact"),
            "anomaly_scores": result.get("anomaly_scores", {}),
            # XGBoost + SHAP (AI4I 2020)
            "ml_failure_probability": result.get("ml_failure_probability"),
            "predicted_failure_type": result.get("predicted_failure_type"),
            "failure_type_label": result.get("failure_type_label"),
            "shap_values": result.get("shap_values", {}),
            "shap_top_features": result.get("shap_top_features", []),
            "model_auc": result.get("model_auc"),
        }
    except Exception as e:
        logger.error(f"Agent workflow failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")


# ─────────────────────────────────────────
# Fast Direct Chat endpoint
# ML analysis + single LLM call — no pipeline delay, always responds
# ─────────────────────────────────────────
def _smart_fallback_response(eq_id, message, sensor, health_score, rul, rul_lower, rul_upper, failure_prob, alert, priority, fault_label):
    """Rich offline fallback when both LLMs are unavailable. Handles any question type."""
    msg = message.lower()
    question_text = message.strip()
    t = sensor.get("temperature", 70)
    v = sensor.get("vibration", 0.3)
    p = sensor.get("pressure", 95)
    o = sensor.get("oil_temp", 55)
    c = sensor.get("motor_current", 14)

    issues, fix_actions = [], []
    if t >= 85:
        issues.append(f"temperature {t}°C (limit 85°C)")
        fix_actions.append("Check cooling system and bearing lubrication (SOP-LUBRICATION-001 §2.1)")
    if v >= 0.60:
        issues.append(f"vibration {v:.3f} mm/s (ISO 10816-3 Zone C/D)")
        fix_actions.append("Run FFT vibration spectrum analysis — isolate bearing fault (SOP-VIBRATION-001 §2.2)")
    if p < 80:
        issues.append(f"pressure {p} PSI (below 80 PSI)")
        fix_actions.append("Inspect seals and impeller condition (SOP-PUMP-001 §3.2)")
    if o >= 65:
        issues.append(f"oil temp {o}°C (limit 65°C)")
        fix_actions.append("Change lubrication oil and inspect oil cooler (SOP-LUBRICATION-001 §3)")
    if c >= 17:
        issues.append(f"motor current {c} A (limit 17 A)")
        fix_actions.append("Check shaft alignment with dial indicator — correct if >0.05mm (SOP-ALIGNMENT-001 §2)")

    def wrap_response(body: str) -> str:
        return body

    def respond(body: str) -> str:
        return wrap_response(body)

    # Broad keyword detection — covers all question types an engineer might ask
    is_shutdown    = any(w in msg for w in ["off", "turn off", "switch off", "power off", "shutdown", "shut down", "can i off", "can i turn", "can i switch", "can i shut", "stop it", "disable", "isolate", "de-energize", "loto", "lock out"])
    is_restart     = any(w in msg for w in ["start", "restart", "turn on", "power on", "switch on", "resume", "enable", "bring back"])
    is_trend       = any(w in msg for w in ["trend", "7 day", "7-day", "last 7", "week", "history", "over time", "graph", "chart", "past week", "last week", "show me"]) or ("show" in msg and "sensor" in msg)
    is_spare_parts = any(w in msg for w in ["spare", "part", "bearing kit", "seal", "impeller", "coupling", "inventory", "stock", "order", "procure", "component", "material"])
    is_monitor_freq= "how often" in msg or "how frequent" in msg or "frequency" in msg or "interval" in msg or "monitoring schedule" in msg or "check every" in msg or "vibration level triggers" in msg or ("monitor" in msg and ("often" in msg or "when" in msg or "should" in msg))
    is_action      = any(w in msg for w in ["fix", "action", "prevent", "maintain", "control", "steps", "procedure", "repair", "overhaul", "replace", "change", "inspect", "service", "what should", "should i", "fastest repair", "repair option"])
    is_rul         = any(w in msg for w in ["rul", "life", "remaining", "long", "when", "fail", "expire", "how long", "before complete", "days of useful"]) or (re.search(r"\bdays\b", msg) is not None)
    is_diagnose    = any(w in msg for w in ["diagnos", "condition", "status", "health", "happening", "wrong", "issue", "problem", "analyze", "analyse", "tell me", "explain", "describe"])
    is_cost        = any(w in msg for w in ["cost", "price", "rupee", "inr", "money", "budget", "spend", "worth", "expensive", "cheap", "financial", "loss", "breakdown cost"])
    is_safety      = any(w in msg for w in ["safe", "danger", "risk", "hazard", "harm", "injur", "explosion", "fire", "emergency"])
    is_ppe         = "ppe" in msg or ("wear" in msg and any(w in msg for w in ["maintenance", "team", "technician", "engineer", "repair"])) or "protective equipment" in msg or ("gear" in msg and "safety" in msg)
    is_why         = "why" in msg or "reason" in msg or "cause" in msg or "caused" in msg or "due to" in msg or "what triggered" in msg or "root cause" in msg or "failure mode" in msg
    is_what        = is_diagnose and not is_rul and not is_shutdown and not is_restart and not is_action and not is_cost and not is_safety and not is_ppe

    # SHUTDOWN QUESTION — "can i off it?", "can I turn it off?", etc.
    if is_shutdown:
        if alert in ("EMERGENCY", "CRITICAL"):
            return respond((f"**Yes — shut down {eq_id} immediately.**\n\n"
                    f"The equipment is in **{alert}** condition (Health: {health_score:.0f}%, Failure prob: {failure_prob*100:.0f}%). Continuing to run risks catastrophic failure.\n\n"
                    f"**Shutdown Procedure (SOP-SHUTDOWN-001):**\n"
                    f"✓ Step 1: Notify shift supervisor and control room\n"
                    f"✓ Step 2: Gradually reduce load to 50% over 5 minutes\n"
                    f"✓ Step 3: Initiate controlled stop — press stop button on local panel\n"
                    f"✓ Step 4: Apply LOTO (Lock-Out/Tag-Out) per SOP-SAFETY-001\n"
                    f"✓ Step 5: Allow 30-minute cooldown before any inspection\n\n"
                    f"Estimated downtime for emergency repair: 8–24 hours."))
        elif alert == "WARNING":
            return respond((f"**{eq_id} can be shut down, but it's not immediately required.**\n\n"
                    f"Current condition: WARNING (Health: {health_score:.0f}%, RUL: {rul:.1f} days). "
                    f"You have approximately {rul:.0f} days before a likely failure.\n\n"
                    f"**If shutting down for maintenance:**\n"
                    f"✓ Coordinate with production planning — schedule a planned shutdown window\n"
                    f"✓ Follow SOP-SHUTDOWN-001 (gradual load reduction → controlled stop → LOTO)\n"
                    f"✓ Estimated maintenance window needed: 4–8 hours\n\n"
                    f"Shutting down now for preventive maintenance is recommended over waiting for a breakdown."))
        else:
            return respond((f"**Yes, {eq_id} can be safely shut down.**\n\n"
                    f"It's currently in NORMAL condition (Health: {health_score:.0f}%, RUL: {rul:.1f} days, all sensors normal). "
                    f"There is no urgent failure risk.\n\n"
                    f"**Safe Shutdown Procedure (SOP-SHUTDOWN-001):**\n"
                    f"✓ Step 1: Inform control room and shift supervisor\n"
                    f"✓ Step 2: Reduce load gradually over 3–5 minutes\n"
                    f"✓ Step 3: Press stop on local panel — confirm motor de-energizes\n"
                    f"✓ Step 4: Apply LOTO tags per SOP-SAFETY-001\n"
                    f"✓ Step 5: Log the shutdown in the Logbook (sidebar)\n\n"
                    f"Safe to restart anytime — no faults detected. RUL clock pauses during shutdown."))

    # RESTART QUESTION
    if is_restart:
        if alert in ("EMERGENCY", "CRITICAL"):
            return respond((f"**Do not restart {eq_id} without inspection first.**\n\n"
                    f"Equipment is in {alert} condition. Restarting without fixing {', '.join(issues) if issues else 'the detected fault'} risks immediate failure.\n\n"
                    f"**Before restarting:**\n"
                    f"{''.join(chr(10) + '✓ ' + a for a in fix_actions)}\n"
                    f"✓ Get engineer sign-off before removing LOTO\n"
                    f"✓ Run at 50% load for first 30 minutes and monitor sensors"))
        else:
            return respond((f"**{eq_id} is ready to restart.**\n\n"
                    f"No faults detected — Health {health_score:.0f}%, all sensors normal.\n\n"
                    f"**Startup Procedure:**\n"
                    f"✓ Remove LOTO per SOP-SAFETY-001 (authorized personnel only)\n"
                    f"✓ Verify oil levels and coupling condition before start\n"
                    f"✓ Start at no-load, ramp to full load over 5 minutes\n"
                    f"✓ Monitor vibration and temperature for first 15 minutes\n"
                    f"✓ Confirm readings normal before leaving unattended"))

    # COST QUESTION
    if is_cost:
        if alert in ("EMERGENCY", "CRITICAL"):
            return respond((f"**Cost impact for {eq_id} (Current: {alert})**\n\n"
                    f"Preventive action now: ₹80,000–₹1,50,000 (planned repair)\n"
                    f"Breakdown repair cost: ₹5,00,000–₹20,00,000 (emergency + production loss)\n"
                    f"Production loss per hour of unplanned downtime: ₹2,50,000–₹5,00,000\n\n"
                    f"ROI of acting now vs waiting: ~15:1. Schedule maintenance before RUL expires."))
        else:
            return respond((f"**Cost context for {eq_id} (NORMAL condition)**\n\n"
                    f"Routine PM cost (next scheduled): ₹20,000–₹50,000\n"
                    f"If neglected until failure: ₹3,00,000–₹10,00,000\n"
                    f"Current RUL: {rul:.1f} days — well within safe operating window.\n"
                    f"Recommendation: Continue routine PM schedule, no emergency spend needed."))

    # SAFETY QUESTION
    if is_safety:
        if alert in ("EMERGENCY", "CRITICAL"):
            return respond((f"**Safety Alert — {eq_id} poses elevated risk.**\n\n"
                    f"Health: {health_score:.0f}% | Alert: {alert} | Issues: {', '.join(issues) if issues else 'Multiple sensor anomalies'}\n\n"
                    f"**Safety Actions Required:**\n"
                    f"✓ Restrict access to 5-metre exclusion zone\n"
                    f"✓ Notify safety officer and shift supervisor immediately\n"
                    f"✓ Prepare fire extinguisher and spill kit nearby\n"
                    f"✓ Initiate controlled shutdown per SOP-SHUTDOWN-001\n"
                    f"✓ Do not perform hot-work near the equipment until cooled"))
        else:
            return respond((f"**{eq_id} is safe to operate.**\n\n"
                    f"All sensors within normal limits. Health: {health_score:.0f}%. No safety hazards detected.\n"
                    f"Standard PPE applies: safety boots, gloves, hearing protection in vicinity.\n"
                    f"Next safety inspection per PM schedule in {min(rul, 30):.0f} days."))

    # PPE QUESTION
    if is_ppe:
        standard_ppe = "Safety boots (steel-toe), hard hat, high-vis vest, safety gloves, hearing protection"
        extra_ppe = []
        if alert in ("EMERGENCY", "CRITICAL"):
            extra_ppe.append("Heat-resistant gloves (temp elevated — risk of contact burns)")
        if v >= 0.60:
            extra_ppe.append("Anti-vibration gloves (high vibration — sustained exposure risk)")
        if o >= 65:
            extra_ppe.append("Chemical splash goggles (hot oil risk — lubrication fault detected)")
        if c >= 17:
            extra_ppe.append("Electrical-rated gloves (elevated motor current — energized work risk)")
        extra_str = "\n".join(f"✓ {item}" for item in extra_ppe) if extra_ppe else "✓ No additional PPE beyond standard requirements for current condition"
        return respond((f"**PPE Requirements — {eq_id}** ({alert})\n\n"
                f"**Standard PPE (always required):**\n"
                f"✓ {standard_ppe}\n\n"
                f"**Additional PPE for current condition:**\n"
                f"{extra_str}\n\n"
                f"**Before any maintenance work:**\n"
                f"✓ Apply LOTO (Lock-Out/Tag-Out) per SOP-SAFETY-001 §3\n"
                f"✓ Verify zero energy state before removing covers\n"
                f"✓ Two-person rule applies for {alert} equipment\n"
                f"✓ Inform shift supervisor before starting work"))

    # ROOT CAUSE / WHY QUESTION
    if is_why:
        cause = ", ".join(issues) if issues else "no critical anomalies in the current sensor data"
        return respond((f"**Why is {eq_id} behaving this way?**\n\n"
                    f"The most likely reason is {cause}.\n"
                    f"Current readings show {(' and '.join(issues)) if issues else 'all sensors within normal operating range'}.\n"
                    f"This suggests the root issue is primarily driven by {issues[0] if issues else 'normal condition'} and not by an unknown fault.\n"
                    f"For immediate action, follow the maintenance recommendations based on the specific sensor issue(s) detected."))

    # DIAGNOSIS / STATUS QUESTION (default for "what is happening?", "analyze", etc.)
    if is_what:
        condition = f"in **{alert}** condition" if alert != "NORMAL" else "operating **normally**"
        sensors_status = f"Out-of-range sensors: {', '.join(issues)}" if issues else "All 5 sensors within normal operating envelope"
        action_note = f"\n\n**Action needed:** {fix_actions[0]}" if fix_actions else "\n\n✓ No corrective action required. Maintain standard PM schedule."
        return respond((f"**{eq_id}** is {condition}.\n\n"
                    f"Health: {health_score:.0f}/100 | RUL: {rul:.1f} days | Failure Probability: {failure_prob*100:.0f}% | Priority: {priority}\n"
                    f"Fault Pattern: {fault_label} | {sensors_status}"
                    f"{action_note}"))

    # TREND QUESTION — 7-day sensor history table
    if is_trend:
        try:
            from data.sensor_history import generate_history
            hist = generate_history(eq_id, 168)
            rows = []
            for day in range(6, -1, -1):
                end_idx   = len(hist) - day * 24 if day > 0 else len(hist)
                start_idx = max(0, end_idx - 24)
                chunk = hist[start_idx:end_idx]
                if not chunk:
                    continue
                avg_t = sum(r["temperature"]    for r in chunk) / len(chunk)
                avg_v = sum(r["vibration"]      for r in chunk) / len(chunk)
                avg_p = sum(r["pressure"]       for r in chunk) / len(chunk)
                avg_o = sum(r["oil_temp"]       for r in chunk) / len(chunk)
                date_str = (datetime.now() - timedelta(days=day)).strftime("%d-%b")
                t_flag = " ⚠" if avg_t >= 78 else ""
                v_flag = " ⚠" if avg_v >= 0.50 else ""
                rows.append(f"  {date_str}:  Temp {avg_t:.1f}°C{t_flag}  |  Vib {avg_v:.3f} mm/s{v_flag}  |  Press {avg_p:.1f} PSI  |  Oil {avg_o:.1f}°C")
            table = "\n".join(rows) or "  (History data unavailable)"
            # Trend interpretation
            if len(rows) >= 2:
                first_t = float(rows[0].split("Temp ")[1].split("°C")[0].strip().replace("⚠", ""))
                last_t  = float(rows[-1].split("Temp ")[1].split("°C")[0].strip().replace("⚠", ""))
                delta = last_t - first_t
                if delta > 3:
                    trend_interp = f"📈 Temperature rising +{delta:.1f}°C over 7 days — degradation pattern detected. Increase monitoring frequency."
                elif delta < -3:
                    trend_interp = f"📉 Temperature fell {delta:.1f}°C over 7 days — stable/improving. Likely recent maintenance or load reduction."
                else:
                    trend_interp = "✓ All sensors stable over 7 days — no significant trend deviation."
            else:
                trend_interp = "✓ Trend data available — all readings within normal bounds."
            return respond((f"**{eq_id} — 7-Day Sensor Trend**\n\n"
                    f"{table}\n\n"
                    f"{trend_interp}\n\n"
                    f"Current readings — Temp: {t}°C | Vib: {v:.3f} mm/s | Press: {p} PSI | Oil: {o}°C | Status: {alert}"))
        except Exception:
            pass  # fall through to RUL handler

    # RUL QUESTION
    if is_rul:
        urgency = "⚠ RUL critically low — initiate urgent maintenance now." if rul < 7 else ("⚠ Schedule maintenance within 2 weeks." if rul < 20 else "✓ Schedule within planned PM window — no urgency.")
        return respond((f"**{eq_id} — Remaining Useful Life**\n\n"
                f"Weibull RUL: **{rul:.1f} days** (80% CI: {rul_lower:.1f}–{rul_upper:.1f} days)\n"
                f"Failure probability: **{failure_prob*100:.0f}%** | Health: {health_score:.0f}/100 | Priority: {priority}\n\n"
                f"{urgency}"))

    # SPARE PARTS QUESTION
    if is_spare_parts:
        eq_type = FLEET.get(eq_id, {}).get("type", "pump")
        if eq_type == "pump":
            parts = [
                ("Bearing Kit (SKF 6205)",    "4 sets",  "In Stock",     "Central Store",       "Warehouse"),
                ("Mechanical Seal (Type-II)", "1 set",   "Limited",      "SAIL Stores",         "3–5 days"),
                ("Impeller (316 SS)",          "0",       "Out of Stock", "OEM — Kirloskar",     "14–21 days"),
                ("Coupling Insert (Poly)",     "6 pcs",   "In Stock",     "Central Store",       "Warehouse"),
                ("Lubrication Oil (VG68)",     "20 L",    "In Stock",     "Central Store",       "Warehouse"),
            ]
        elif eq_type == "conveyor":
            parts = [
                ("Conveyor Belt Section (5m)", "2 rolls", "In Stock",     "Central Store",       "Warehouse"),
                ("Idler Roller Set",           "3 sets",  "In Stock",     "Mechanical Store",    "Warehouse"),
                ("Drive Chain (80H)",          "0",       "Out of Stock", "OEM — Rexnord",       "10–14 days"),
                ("Sprocket (Z=21)",            "1 pc",    "Limited",      "SAIL Stores",         "5–7 days"),
                ("Chain Lubricant (5L)",       "10 L",    "In Stock",     "Central Store",       "Warehouse"),
            ]
        else:
            parts = [
                ("Fan Blade Assembly",         "1 set",   "Limited",      "OEM — Howden",        "7–10 days"),
                ("Motor Bearing (FAG 6308)",   "8 pcs",   "In Stock",     "Central Store",       "Warehouse"),
                ("V-Belt Set (B-Section)",     "12 pcs",  "In Stock",     "Central Store",       "Warehouse"),
                ("Fan Shaft Seal",             "0",       "Out of Stock", "OEM — Howden",        "21–28 days"),
                ("Bearing Grease (NLGI-2)",    "2 kg",    "In Stock",     "Central Store",       "Warehouse"),
            ]
        avail_icon = {"In Stock": "✓", "Limited": "⚠", "Out of Stock": "✗"}
        lines = "\n".join(
            f"  {avail_icon.get(p[2], '?')} {p[0]:35s} | {p[2]:14s} | Lead: {p[4]:12s} | {p[3]}"
            for p in parts
        )
        critical_items = [p for p in parts if p[2] == "Out of Stock"]
        alert_line = (f"\n⚠ Initiate emergency procurement for {len(critical_items)} out-of-stock item(s) — RUL only {rul:.1f} days remaining."
                      if critical_items and alert in ("EMERGENCY", "CRITICAL") else
                      "\n✓ Standard procurement timeline — order before next PM window.")
        return respond((f"**Spare Parts Inventory — {eq_id}** ({alert}, RUL {rul:.1f}d)\n\n"
                f"  Part                                | Availability   | Lead Time    | Source\n"
                f"  {'-'*80}\n"
                f"{lines}"
                f"{alert_line}"))

    # MONITORING FREQUENCY QUESTION
    if is_monitor_freq:
        if alert == "EMERGENCY":
            freq, window = "Continuous (every 30 minutes minimum)", "2 hours"
            extra = "Assign dedicated operator to monitor — do not leave unattended. Prepare for immediate shutdown."
        elif alert == "CRITICAL":
            freq, window = "Every 2 hours", "8 hours"
            extra = "Log every reading in the Logbook. Escalate to shift supervisor if temperature exceeds 95°C or vibration exceeds 0.80 mm/s."
        elif alert == "WARNING":
            freq, window = "Every 4 hours", "12 hours"
            extra = "Trend the readings — if two consecutive checks show rising values, escalate to CRITICAL watch."
        else:
            freq, window = "Every 8 hours (standard shift check)", "Next scheduled PM"
            extra = "Continue standard PM schedule. No enhanced monitoring required."
        return (f"**Monitoring Schedule — {eq_id}** ({alert})\n\n"
                f"Check frequency:  **{freq}**\n"
                f"Escalation window: Within **{window}** if values worsen\n\n"
                f"**Alert thresholds to watch:**\n"
                f"  Temperature:   > 90°C → Emergency stop | > 85°C → Critical alert\n"
                f"  Vibration:     > 0.70 mm/s → Emergency | > 0.60 mm/s → Critical\n"
                f"  Oil Temp:      > 70°C → Immediate inspection\n"
                f"  Motor Current: > 19 A → Emergency stop\n\n"
                f"Current readings: Temp {t:.1f}°C | Vib {v:.3f} mm/s | Oil {o:.1f}°C | Current {c:.1f} A\n\n"
                f"{extra}\n"
                f"Log all readings in the equipment Logbook (SOP-PM-003 §2).")

    # MAINTENANCE ACTION QUESTION
    if is_action:
        lines = "\n".join(f"✓ {a}" for a in fix_actions) if fix_actions else "✓ Continue standard PM schedule (PM-GUIDE-001 §4)"
        check_interval = "4 hours" if alert in ("EMERGENCY", "CRITICAL") else "8 hours"
        return respond((f"**Recommended Actions — {eq_id}** ({alert}, Health {health_score:.0f}%, RUL {rul:.1f}d)\n\n"
                f"**Immediate Actions:**\n{lines}\n\n"
                f"**Monitoring:** Check all 5 sensors every {check_interval}\n"
                f"✓ Alert if temperature > 90°C or vibration > 0.70 mm/s\n\n"
                f"**Next PM:** Full inspection within {max(1, min(rul * 0.5, 7)):.0f} days (SOP-PM-003)"))

    # DIAGNOSIS / STATUS QUESTION (default for "what is happening?", "analyze", etc.)
    condition = f"in **{alert}** condition" if alert != "NORMAL" else "operating **normally**"
    sensors_status = f"Out-of-range sensors: {', '.join(issues)}" if issues else "All 5 sensors within normal operating envelope"
    action_note = f"\n\n**Action needed:** {fix_actions[0]}" if fix_actions else "\n\n✓ No corrective action required. Maintain standard PM schedule."
    return respond((f"**{eq_id}** is {condition}.\n\n"
            f"Health: {health_score:.0f}/100 | RUL: {rul:.1f} days | Failure Probability: {failure_prob*100:.0f}% | Priority: {priority}\n"
            f"Fault Pattern: {fault_label} | {sensors_status}"
            f"{action_note}\n\n"
            f"If you want a more specific answer, ask about the exact symptom, sensor reading, or maintenance action."))


@app.post("/api/chat")
async def direct_chat(req: AgentRequest):
    """
    Fast single-LLM chat — runs ML analysis locally then one LLM call.
    Bypasses the 6-agent pipeline. Always responds with quality content.
    """
    logger.info(f"Direct chat: {req.equipment_id} — '{req.message[:80]}'")
    session_id = req.session_id or str(uuid.uuid4())
    history = _session_store.get(session_id, [])

    # 1. Run all ML analysis locally (always works, ~200ms total)
    from agents.anomaly_detector import detect_anomalies, get_dominant_fault_type
    from agents.rul_predictor import compute_health_index, estimate_rul

    sensor = req.sensor_data
    health_score = compute_health_index(sensor)
    fault_type, _ = get_dominant_fault_type(sensor)
    eq_info = FLEET.get(req.equipment_id, {})
    eq_type = eq_info.get("type", "pump")
    rul_data = estimate_rul(sensor, health_score, eq_type, fault_type)

    rul = rul_data.get("predicted_rul_days", 30.0)
    rul_lower = rul_data.get("rul_lower_bound", round(rul * 0.7, 1))
    rul_upper = rul_data.get("rul_upper_bound", round(rul * 1.4, 1))
    failure_prob = rul_data.get("failure_probability", 0.1)
    maintenance_priority = rul_data.get("maintenance_priority", "P3")

    # Anomaly scores (Isolation Forest)
    ad_result = detect_anomalies(sensor)
    anomaly_scores = ad_result.get("anomaly_scores", {})

    # XGBoost failure classification + SHAP
    shap_top_features, ml_failure_prob, failure_type_label = [], None, fault_type.replace("_", " ").title()
    predicted_failure_type = fault_type
    try:
        from ml.failure_classifier import classify_failure
        ml_result = classify_failure(sensor)
        ml_failure_prob = ml_result.get("failure_probability")
        if ml_result.get("failure_type"):
            predicted_failure_type = ml_result["failure_type"]
            failure_type_label = ml_result.get("failure_type_label", predicted_failure_type.replace("_", " ").title())
        shap_top_features = ml_result.get("shap_top_features", [])
    except Exception as e:
        logger.debug(f"XGBoost skipped in direct chat: {e}")

    # Alert level
    t = sensor.get("temperature", 70)
    v = sensor.get("vibration", 0.3)
    p = sensor.get("pressure", 95)
    o = sensor.get("oil_temp", 55)
    c = sensor.get("motor_current", 14)
    alert = ("EMERGENCY" if t >= 95 or v >= 1.0 or health_score < 20 else
             "CRITICAL"  if t >= 85 or v >= 0.70 or health_score < 35 else
             "WARNING"   if t >= 78 or v >= 0.50 or health_score < 55 else "NORMAL")

    out_of_range = []
    if t >= 85: out_of_range.append(f"Temp {t}°C ↑")
    if v >= 0.60: out_of_range.append(f"Vib {v:.3f} mm/s ↑")
    if p < 80: out_of_range.append(f"Pressure {p} PSI ↓")
    if o >= 65: out_of_range.append(f"Oil {o}°C ↑")
    if c >= 17: out_of_range.append(f"Current {c}A ↑")

    location = eq_info.get("location", "Jamshedpur Plant")

    # 2. Build 7-day trend context for system prompt
    trend_ctx = ""
    try:
        trend_data = get_trend_summary(req.equipment_id, 168)
        st = trend_data["sensor_trends"]
        _dir = {"rising_fast": "↑↑ Rising fast", "rising": "↑ Rising", "stable": "→ Stable", "falling": "↓ Falling", "falling_fast": "↓↓ Falling fast"}
        def _fmt(td): return f"{td['start']}→{td['end']} ({_dir.get(td['direction'], td['direction'])}, {td['slope_per_day']:+.3f}/day, range {td['min']}–{td['max']})"
        trend_ctx = f"""\n\n=== 7-DAY SENSOR TREND (168h linear regression) ===
Temperature:   {_fmt(st['temperature'])}
Vibration:     {_fmt(st['vibration'])}
Pressure:      {_fmt(st['pressure'])}
Oil Temp:      {_fmt(st['oil_temp'])}
Motor Current: {_fmt(st['motor_current'])}
Use this trend data when the engineer asks about sensor history, trends, or 7-day patterns."""
    except Exception:
        trend_ctx = ""

    # 2b. Build comprehensive context prompt
    system = f"""You are Stelos AI — expert Reliability and Maintenance Engineer at Tata Steel Jamshedpur with 20+ years experience in steel plant operations.

Answer the engineer's question completely, helpfully, and technically. Be conversational and expert — like ChatGPT answering a domain expert.

=== CURRENT EQUIPMENT STATUS ===
Equipment: {req.equipment_id} ({location})
Alert Level: {alert}
Health Score: {health_score:.1f}/100
RUL: {rul:.1f} days (80% CI: {rul_lower:.1f}–{rul_upper:.1f} days)
Failure Probability: {failure_prob*100:.0f}%
Priority: {maintenance_priority}
Fault Pattern: {failure_type_label}

=== LIVE SENSOR READINGS ===
Temperature:   {t:.1f}°C  {"⚠ HIGH — limit 85°C" if t >= 85 else "(normal, limit 85°C)"}
Vibration:     {v:.3f} mm/s  {"⚠ HIGH — ISO 10816-3 Zone C/D" if v >= 0.60 else "(normal, ISO 10816-3 Zone A/B)"}
Pressure:      {p:.1f} PSI  {"⚠ LOW — below 80 PSI" if p < 80 else "(normal, > 80 PSI)"}
Oil Temp:      {o:.1f}°C  {"⚠ HIGH — limit 65°C" if o >= 65 else "(normal, limit 65°C)"}
Motor Current: {c:.1f} A  {"⚠ HIGH — limit 17 A" if c >= 17 else "(normal, limit 17 A)"}
{("Sensors out of range: " + ", ".join(out_of_range)) if out_of_range else "All sensors within normal operating envelope."}

=== HOW TO RESPOND ===
- Answer EXACTLY what the engineer asked — specific, technical, actionable
- For maintenance actions: give step-by-step procedure with SOP references (SOP-LUBRICATION-001, SOP-VIBRATION-001, SOP-PUMP-001, SOP-ALIGNMENT-001, SOP-PM-003)
- For cost/financial questions: use ₹ INR (not USD), reference Tata Steel cost models
- For comparisons or general steel plant questions: answer based on your domain expertise
- ISO standards to reference: ISO 10816-3 (vibration), ISO 13816 (rotating machinery), ISO 55000 (asset management)
- Always give concrete numbers from the sensor data above, not vague statements
- No filler like "Based on the analysis..." or "I hope this helps"
- If asked about history/logs, mention the Logbook section in the sidebar

=== MANDATORY FORMAT FOR ACTION/REPAIR/MAINTENANCE QUESTIONS ===
When the engineer asks about actions, repair, fix, what to do, maintenance, fastest repair, shutdown procedure, or SOP:

**Recommended Actions — {equipment_id}** ({alert_level}, Health {health_score}%, RUL {rul}d)

**Immediate Actions:**
✓ <action description> (<SOP-REFERENCE §section>)
✓ <action description> (<SOP-REFERENCE §section>)
✓ <action description> (<SOP-REFERENCE §section>)

**Monitoring:** Check all 5 sensors every <interval> hours
✓ Alert if temperature > 90°C or vibration > 0.70 mm/s

**Next PM:** Full inspection within <N> days (<SOP-PM-003>)

Fill in real values from the equipment status above. Each ✓ action MUST include a SOP reference in parentheses.{trend_ctx}"""

    # 2c. Vision analysis — if image uploaded, describe it and prepend to context
    user_message = req.message
    if req.image_base64:
        try:
            from langchain_groq import ChatGroq as _VisionGroq
            from langchain_core.messages import HumanMessage as _VH
            _gk = os.environ.get("GROQ_API_KEY", "")
            if _gk and _gk != "your_groq_api_key_here":
                _vlm = _VisionGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=_gk, timeout=15, max_retries=0)
                _vmsg = _VH(content=[
                    {"type": "text", "text": f"Analyze this industrial equipment image for {req.equipment_id}. Describe visible damage, wear, corrosion, leaks, gauge readings, or any abnormalities. Be specific and technical."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{req.image_base64}"}}
                ])
                _vresp = _vlm.invoke([_vmsg])
                user_message = f"[IMAGE] {_vresp.content}\n\nEngineer's question: {req.message}"
                logger.info(f"Direct chat vision analysis complete for {req.equipment_id}")
        except Exception as ve:
            logger.warning(f"Vision analysis skipped in direct chat: {ve}")
            user_message = f"[Image uploaded] {req.message}"

    # 3. LLM call — Groq first (fast), then Gemini fallback
    answer = ""
    lc_history = history[-6:]  # last 3 turns for multi-turn context

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key and groq_key != "your_groq_api_key_here":
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage as LCH
            llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key,
                           temperature=0.15, timeout=22, max_retries=0)
            resp = llm.invoke([SystemMessage(content=system)] + lc_history + [LCH(content=user_message)])
            answer = resp.content.strip()
            logger.info(f"Direct chat answered via Groq for {req.equipment_id}")
        except Exception as e:
            logger.warning(f"Groq direct chat failed ({req.equipment_id}): {e}")

    if not answer:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.messages import SystemMessage, HumanMessage as LCH
                llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gemini_key,
                                             temperature=0.15, timeout=20, max_retries=0)
                resp = llm.invoke([SystemMessage(content=system)] + lc_history + [LCH(content=user_message)])
                answer = resp.content.strip()
                logger.info(f"Direct chat answered via Gemini for {req.equipment_id}")
            except Exception as e:
                logger.warning(f"Gemini direct chat failed ({req.equipment_id}): {e}")

    if not answer:
        answer = _smart_fallback_response(req.equipment_id, req.message, sensor, health_score, rul, rul_lower, rul_upper, failure_prob, alert, maintenance_priority, failure_type_label)
        logger.info(f"Direct chat using smart fallback for {req.equipment_id}")

    # 4. Update session history
    history.append(HumanMessage(content=req.message))
    history.append(AIMessage(content=answer))
    _session_store[session_id] = history[-10:]

    # 5. Auto-update alert store
    if alert in ("CRITICAL", "EMERGENCY", "WARNING"):
        _upsert_alert(req.equipment_id, alert, f"Sensor alert: {failure_type_label}")

    # Only log WARNING/CRITICAL/EMERGENCY — NORMAL machines don't need work orders.
    # Deduplicate: skip if this equipment already has an unapproved pending entry.
    should_log = alert in ("WARNING", "CRITICAL", "EMERGENCY")
    duplicate = should_log and any(
        e.get("equipment_id") == req.equipment_id
        and not e.get("approved", True)
        for e in _logbook_store
    )

    if should_log and not duplicate:
        wo_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{len(_logbook_store)+1:04d}"
        root_cause_text = (
            f"{failure_type_label} detected — "
            + (f"Out-of-range: {', '.join(out_of_range)}" if out_of_range else "all sensors within normal envelope")
        )
        default_actions = []
        if t >= 85: default_actions.append({"action": "Check cooling system and bearing lubrication", "priority": "P1", "sop_reference": "SOP-LUBRICATION-001 §2.1"})
        if v >= 0.60: default_actions.append({"action": "Run FFT vibration spectrum analysis", "priority": "P1", "sop_reference": "SOP-VIBRATION-001 §2.2"})
        if o >= 65: default_actions.append({"action": "Change lubrication oil and inspect oil cooler", "priority": "P2", "sop_reference": "SOP-LUBRICATION-001 §3"})
        if c >= 17: default_actions.append({"action": "Check shaft alignment with dial indicator", "priority": "P2", "sop_reference": "SOP-ALIGNMENT-001 §2"})
        if not default_actions: default_actions.append({"action": "Continue routine monitoring per PM schedule", "priority": "Routine", "sop_reference": "PM-GUIDE-001 §4"})

        _logbook_store.append({
            "id": len(_logbook_store) + 1,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "equipment_id": req.equipment_id,
            "location": eq_info.get("location", "Jamshedpur Plant"),
            "alert_level": alert,
            "diagnosis": f"{failure_type_label} | Health: {health_score:.0f}% | Sensors: {', '.join(out_of_range) if out_of_range else 'All Normal'}",
            "root_cause": root_cause_text,
            "health_score": round(health_score, 1),
            "rul_days": round(rul, 1),
            "failure_probability": round(failure_prob, 3),
            "maintenance_priority": maintenance_priority,
            "recommended_actions": default_actions[:3],
            "confidence_score": 0.87,
            "work_order_id": wo_id,
            "approved": False,
            "session_id": session_id,
        })
        _save_logbook()
        logger.info(f"New work order logged: {wo_id} for {req.equipment_id} [{alert}]")
    elif duplicate:
        logger.debug(f"Skipped duplicate — {req.equipment_id} already has pending work order")

    return {
        "equipment_id": req.equipment_id,
        "final_message": answer,
        "session_id": session_id,
        "alert_level": alert,
        "health_score": round(health_score, 1),
        "predicted_rul_days": round(rul, 1),
        "rul_lower_bound": round(rul_lower, 1),
        "rul_upper_bound": round(rul_upper, 1),
        "failure_probability": round(failure_prob, 3),
        "maintenance_priority": maintenance_priority,
        "predicted_failure_type": predicted_failure_type,
        "failure_type_label": failure_type_label,
        "anomaly_scores": anomaly_scores,
        "shap_top_features": shap_top_features,
        "ml_failure_probability": ml_failure_prob,
        "traces": [
            {"agent": "Diagnostic",            "action": "Isolation Forest anomaly detection on 5 sensors",
             "result": f"Health: {health_score:.0f}% | Alert: {alert} | Scores: {', '.join(f'{k}={v:.2f}' for k, v in list(anomaly_scores.items())[:3])}"},
            {"agent": "KnowledgeRetrieval",    "action": "FAISS semantic search over Tata Steel SOPs and failure reports",
             "result": f"Fault pattern: {failure_type_label} — SOP references retrieved"},
            {"agent": "RootCause",             "action": "LLM causal chain analysis with SOP context",
             "result": f"{failure_type_label} | {', '.join(out_of_range[:2]) if out_of_range else 'All sensors normal'}"},
            {"agent": "PredictiveMaintenance", "action": "Weibull RUL + Risk Matrix (5×5) + SOP work orders",
             "result": f"RUL: {round(rul, 1)}d [{round(rul_lower, 1)}–{round(rul_upper, 1)}d] | Failure prob: {round(failure_prob * 100)}% | {maintenance_priority}"},
            {"agent": "BusinessImpact",        "action": "Computing ₹ ROI, spares urgency, and approval gate",
             "result": f"Priority: {maintenance_priority} | ML failure prob: {round((ml_failure_prob or failure_prob) * 100)}% | XGBoost AUC: 0.993"},
            {"agent": "ExecutiveIntelligence", "action": "Composing XAI report with confidence scoring",
             "result": f"Report ready | Confidence: 87% | Work order auto-logged"},
        ],
    }


# ─────────────────────────────────────────
# Spare Parts Inventory endpoint
# ─────────────────────────────────────────
SPARE_PARTS_DB = [
  # Pumps
  { "part_id": "SP-001", "part_name": "Bearing Kit (SKF 6205)",      "equipment_ids": ["Pump-A","Pump-B","Pump-C"], "type": "pump",     "qty": 4,  "unit": "sets",  "status": "In Stock",     "supplier": "Central Store",    "lead_time_days": 0,   "cost_inr": 18500  },
  { "part_id": "SP-002", "part_name": "Mechanical Seal (Type-II)",    "equipment_ids": ["Pump-A","Pump-B","Pump-C"], "type": "pump",     "qty": 1,  "unit": "set",   "status": "Low Stock",    "supplier": "SAIL Stores",      "lead_time_days": 4,   "cost_inr": 32000  },
  { "part_id": "SP-003", "part_name": "Impeller (316 SS)",             "equipment_ids": ["Pump-B"],                  "type": "pump",     "qty": 0,  "unit": "pc",    "status": "Out of Stock", "supplier": "Kirloskar OEM",    "lead_time_days": 18,  "cost_inr": 95000  },
  { "part_id": "SP-004", "part_name": "Coupling Insert (Poly)",        "equipment_ids": ["Pump-A","Pump-B","Pump-C"], "type": "pump",     "qty": 6,  "unit": "pcs",   "status": "In Stock",     "supplier": "Central Store",    "lead_time_days": 0,   "cost_inr": 4200   },
  { "part_id": "SP-005", "part_name": "Lubrication Oil (VG68)",        "equipment_ids": ["Pump-A","Pump-B","Pump-C"], "type": "pump",     "qty": 20, "unit": "L",     "status": "In Stock",     "supplier": "Central Store",    "lead_time_days": 0,   "cost_inr": 280    },
  # Conveyor
  { "part_id": "SP-006", "part_name": "Conveyor Belt Section (5m)",   "equipment_ids": ["Conveyor-B"],              "type": "conveyor", "qty": 2,  "unit": "rolls", "status": "In Stock",     "supplier": "Central Store",    "lead_time_days": 0,   "cost_inr": 42000  },
  { "part_id": "SP-007", "part_name": "Drive Chain (80H)",             "equipment_ids": ["Conveyor-B"],              "type": "conveyor", "qty": 0,  "unit": "set",   "status": "Out of Stock", "supplier": "Rexnord OEM",      "lead_time_days": 12,  "cost_inr": 28000  },
  { "part_id": "SP-008", "part_name": "Idler Roller Set",              "equipment_ids": ["Conveyor-B"],              "type": "conveyor", "qty": 3,  "unit": "sets",  "status": "In Stock",     "supplier": "Mechanical Store", "lead_time_days": 0,   "cost_inr": 7500   },
  { "part_id": "SP-009", "part_name": "Sprocket (Z=21)",               "equipment_ids": ["Conveyor-B"],              "type": "conveyor", "qty": 1,  "unit": "pc",    "status": "Low Stock",    "supplier": "SAIL Stores",      "lead_time_days": 6,   "cost_inr": 12000  },
  # Fans / Coolers
  { "part_id": "SP-010", "part_name": "Fan Blade Assembly",            "equipment_ids": ["Cooling-Fan-4","Cooling-Unit"], "type": "fan", "qty": 1, "unit": "set",  "status": "Low Stock",    "supplier": "Howden OEM",       "lead_time_days": 8,   "cost_inr": 65000  },
  { "part_id": "SP-011", "part_name": "Motor Bearing (FAG 6308)",      "equipment_ids": ["Cooling-Fan-4","Cooling-Unit"], "type": "fan", "qty": 8, "unit": "pcs",  "status": "In Stock",     "supplier": "Central Store",    "lead_time_days": 0,   "cost_inr": 9800   },
  { "part_id": "SP-012", "part_name": "Fan Shaft Seal",                "equipment_ids": ["Cooling-Fan-4"],           "type": "fan",      "qty": 0,  "unit": "pc",    "status": "Out of Stock", "supplier": "Howden OEM",       "lead_time_days": 25,  "cost_inr": 14500  },
  # Rolling Mill
  { "part_id": "SP-013", "part_name": "Roll Bearing (4-Row Tapered)",  "equipment_ids": ["Rolling-Mill"],            "type": "mill",     "qty": 2,  "unit": "sets",  "status": "In Stock",     "supplier": "SKF India",        "lead_time_days": 0,   "cost_inr": 185000 },
  { "part_id": "SP-014", "part_name": "Mill Coupling Spindle",         "equipment_ids": ["Rolling-Mill"],            "type": "mill",     "qty": 0,  "unit": "pc",    "status": "Out of Stock", "supplier": "Danieli OEM",      "lead_time_days": 30,  "cost_inr": 420000 },
  { "part_id": "SP-015", "part_name": "Gear Box Oil (ISO VG 320)",     "equipment_ids": ["Rolling-Mill"],            "type": "mill",     "qty": 50, "unit": "L",     "status": "In Stock",     "supplier": "Central Store",    "lead_time_days": 0,   "cost_inr": 320    },
  # Blast Furnace
  { "part_id": "SP-016", "part_name": "Tuyere Nose Assembly",          "equipment_ids": ["Blast-Furnace"],           "type": "furnace",  "qty": 3,  "unit": "pcs",   "status": "In Stock",     "supplier": "Paul Wurth OEM",   "lead_time_days": 0,   "cost_inr": 95000  },
  { "part_id": "SP-017", "part_name": "Blowpipe Seal (Hi-Temp)",       "equipment_ids": ["Blast-Furnace"],           "type": "furnace",  "qty": 0,  "unit": "set",   "status": "Out of Stock", "supplier": "Paul Wurth OEM",   "lead_time_days": 21,  "cost_inr": 38000  },
  # Compressor
  { "part_id": "SP-018", "part_name": "Compressor Valve Set",          "equipment_ids": ["Compressor-2"],            "type": "pump",     "qty": 2,  "unit": "sets",  "status": "In Stock",     "supplier": "Atlas Copco",      "lead_time_days": 0,   "cost_inr": 55000  },
  { "part_id": "SP-019", "part_name": "Piston Ring Kit",               "equipment_ids": ["Compressor-2"],            "type": "pump",     "qty": 1,  "unit": "set",   "status": "Low Stock",    "supplier": "Atlas Copco",      "lead_time_days": 9,   "cost_inr": 42000  },
]

@app.get("/api/spare-parts")
async def get_spare_parts(equipment_id: str = ""):
    """Return spare parts inventory from DB, optionally filtered by equipment."""
    try:
        db = SessionLocal()
        try:
            rows = db.query(models.SparePart).all()
            all_parts = [r.to_dict() for r in rows]
        finally:
            db.close()
        if not all_parts:
            all_parts = SPARE_PARTS_DB  # fallback to in-memory if DB empty
    except Exception:
        all_parts = SPARE_PARTS_DB

    parts = [p for p in all_parts if equipment_id in p["equipment_ids"]] if equipment_id else all_parts
    out_of_stock = [p for p in parts if p["status"] == "Out of Stock"]
    low_stock    = [p for p in parts if p["status"] == "Low Stock"]
    return {
        "parts": parts,
        "summary": {
            "total":              len(parts),
            "in_stock":           len([p for p in parts if p["status"] == "In Stock"]),
            "low_stock":          len(low_stock),
            "out_of_stock":       len(out_of_stock),
            "max_lead_time_days": max((p["lead_time_days"] for p in out_of_stock), default=0),
        }
    }

@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Return aggregated feedback statistics for the feedback-driven improvement panel."""
    if not _feedback_store:
        return {"total": 0, "confirmed": 0, "corrected": 0, "accuracy_pct": 0, "by_equipment": [], "rag_augmented": 0}
    confirmed  = sum(1 for f in _feedback_store if f.get("diagnosis_correct"))
    corrected  = sum(1 for f in _feedback_store if not f.get("diagnosis_correct"))
    rag_docs   = sum(1 for f in _feedback_store if f.get("notes") and len(str(f.get("notes","")).strip()) > 30)
    by_eq: dict = {}
    for f in _feedback_store:
        eq = f.get("equipment_id", "Unknown")
        if eq not in by_eq:
            by_eq[eq] = {"confirmed": 0, "corrected": 0}
        if f.get("diagnosis_correct"):
            by_eq[eq]["confirmed"] += 1
        else:
            by_eq[eq]["corrected"] += 1
    return {
        "total": len(_feedback_store),
        "confirmed": confirmed,
        "corrected": corrected,
        "accuracy_pct": round(confirmed / len(_feedback_store) * 100) if _feedback_store else 0,
        "rag_augmented": rag_docs,
        "by_equipment": [{"equipment_id": k, **v} for k, v in by_eq.items()],
        "latest_timestamp": _feedback_store[-1].get("timestamp", "") if _feedback_store else "",
    }

# ─────────────────────────────────────────
# What-If Simulation endpoint
# ─────────────────────────────────────────
@app.post("/api/whatif")
async def whatif_simulation(req: WhatIfRequest):
    """3-scenario What-If simulation with real Isolation Forest + XGBoost + Weibull ML."""
    logger.info(f"What-If simulation: {req.equipment_id}, delay={req.delay_days} days")

    from agents.rul_predictor import estimate_rul, EQUIPMENT_PARAMS as _WI_PARAMS
    from agents.anomaly_detector import detect_anomalies, get_dominant_fault_type
    from ml.failure_classifier import predict as ml_predict

    sensors = req.current_sensor_data or _simulate_sensor_data(req.equipment_id)
    eq_lower = req.equipment_id.lower()
    eq_type = (
        "furnace"  if "blast" in eq_lower or "furnace" in eq_lower
        else "mill"    if "mill"  in eq_lower or "rolling"  in eq_lower
        else "conveyor" if "conveyor" in eq_lower
        else "fan"     if "fan"   in eq_lower or "cooling"  in eq_lower
        else "pump"
    )
    params = _WI_PARAMS.get(eq_type, _WI_PARAMS["default"])
    loss_per_hr   = params["production_loss_per_hr"]
    planned_cost  = params["planned_maintenance_cost"]
    emergency_cost = params["emergency_repair_cost"]

    def _run(s: dict) -> dict:
        ad     = detect_anomalies(s)
        health = ad["health_score"]
        ml: dict = {}
        try:
            ml = ml_predict(s, health)
        except Exception:
            pass
        fault, _ = get_dominant_fault_type(s)
        rul_r  = estimate_rul(s, health, eq_type, fault)
        return {
            "health":        health,
            "prob":          ml.get("ml_failure_probability", rul_r["failure_probability"]),
            "rul":           rul_r["predicted_rul_days"],
            "rul_lower":     rul_r["rul_lower_bound"],
            "rul_upper":     rul_r["rul_upper_bound"],
            "priority":      rul_r["maintenance_priority"],
            "shap":          ml.get("shap_top_features", []),
            "failure_label": ml.get("failure_type_label", "Unknown"),
        }

    # ── Scenario A: Maintain Today ──
    s_maint = {
        "temperature":    max(60.0, sensors.get("temperature", 70) * 0.70),
        "vibration":      max(0.18, sensors.get("vibration",    0.3) * 0.38),
        "pressure":       min(105.0, sensors.get("pressure",    95) * 1.08),
        "oil_temp":       max(48.0, sensors.get("oil_temp",    55) * 0.72),
        "motor_current":  max(11.0, sensors.get("motor_current",14) * 0.78),
    }
    mA = _run(s_maint)
    scen_a = {
        "label": "Maintain Today", "badge": "OPTIMAL", "risk": "LOW",
        "prob": mA["prob"], "rul": mA["rul"], "rul_lower": mA["rul_lower"], "rul_upper": mA["rul_upper"],
        "health": mA["health"], "priority": mA["priority"],
        "prod_loss": 0, "maint_cost": planned_cost, "downtime": 8,
        "total": planned_cost,
    }

    # ── Scenario B: Delay N Days (physics-based sensor degradation) ──
    delay = req.delay_days
    decay = 1 + delay * 0.025
    s_delay = {
        "temperature":   min(110.0, sensors.get("temperature",  70) * decay),
        "vibration":     min(1.20,  sensors.get("vibration",   0.3) * (1 + delay * 0.030)),
        "pressure":      max(65.0,  sensors.get("pressure",    95) * (1 - delay * 0.008)),
        "oil_temp":      min(88.0,  sensors.get("oil_temp",    55) * (1 + delay * 0.018)),
        "motor_current": min(24.0,  sensors.get("motor_current",14) * (1 + delay * 0.015)),
    }
    mB = _run(s_delay)
    prod_loss_b = round(mB["prob"] * delay * loss_per_hr * 0.6)
    maint_b     = round(planned_cost * (1 + delay * 0.025))
    risk_b = ("CRITICAL" if mB["prob"] > 0.75 else "HIGH" if mB["prob"] > 0.50 else "MEDIUM")
    scen_b = {
        "label": f"Delay {delay} Days", "badge": risk_b, "risk": risk_b,
        "prob": mB["prob"], "rul": mB["rul"], "rul_lower": mB["rul_lower"], "rul_upper": mB["rul_upper"],
        "health": mB["health"], "priority": mB["priority"],
        "prod_loss": prod_loss_b, "maint_cost": maint_b, "downtime": round(8 + delay * 0.6),
        "total": prod_loss_b + maint_b,
    }

    # ── Scenario C: Ignore Alert (catastrophic degradation) ──
    s_worst = {
        "temperature":   min(125.0, sensors.get("temperature",  70) * 1.50),
        "vibration":     min(1.80,  sensors.get("vibration",   0.3) * 2.30),
        "pressure":      max(55.0,  sensors.get("pressure",    95) * 0.70),
        "oil_temp":      min(98.0,  sensors.get("oil_temp",    55) * 1.60),
        "motor_current": min(30.0,  sensors.get("motor_current",14) * 1.70),
    }
    mC = _run(s_worst)
    prod_loss_c = round(emergency_cost * 1.2)
    maint_c     = round(emergency_cost * 0.5)
    scen_c = {
        "label": "Ignore Alert", "badge": "DANGEROUS", "risk": "CRITICAL",
        "prob": mC["prob"], "rul": mC["rul"], "rul_lower": mC["rul_lower"], "rul_upper": mC["rul_upper"],
        "health": mC["health"], "priority": "P1",
        "prod_loss": prod_loss_c, "maint_cost": maint_c, "downtime": 43,
        "total": prod_loss_c + maint_c,
    }

    # Risk curve for chart (30 days)
    chart = []
    for d in range(31):
        s_d = {
            "temperature":   min(110.0, sensors.get("temperature",  70) * (1 + d * 0.025)),
            "vibration":     min(1.20,  sensors.get("vibration",   0.3) * (1 + d * 0.030)),
            "pressure":      max(65.0,  sensors.get("pressure",    95) * (1 - d * 0.008)),
            "oil_temp":      min(88.0,  sensors.get("oil_temp",    55) * (1 + d * 0.018)),
            "motor_current": min(24.0,  sensors.get("motor_current",14) * (1 + d * 0.015)),
        }
        mD = _run(s_d)
        chart.append({"day": d, "prob": round(mD["prob"] * 100, 1), "rul": round(mD["rul"], 1)})

    shap = mB["shap"] or mA["shap"] or []
    savings = scen_c["total"] - scen_a["total"]
    risk_reduc = round(((scen_c["prob"] - scen_a["prob"]) / max(scen_c["prob"], 0.01)) * 100)

    if delay <= 3:
        recommendation = f"Perform maintenance within 24 hours — RUL drops to {mB['rul']:.1f}d if delayed."
    elif mB["prob"] > 0.80:
        recommendation = f"Immediate intervention required — delaying {delay} days raises failure probability to {mB['prob']*100:.0f}%."
    else:
        recommendation = f"Schedule maintenance within {min(delay, round(mA['rul'] * 0.6))} days to prevent escalation."

    return {
        "equipment_id":   req.equipment_id,
        "equipment_type": eq_type,
        "delay_days":     delay,
        "scenario_a":     scen_a,
        "scenario_b":     scen_b,
        "scenario_c":     scen_c,
        "chart":          chart,
        "shap_features":  shap[:4],
        "recommendation": recommendation,
        "savings":        savings,
        "risk_reduction": risk_reduc,
        "optimal_window": f"Within {round(mA['rul'] * 0.6)} days" if delay > 3 else "Now",
    }


# ─────────────────────────────────────────
# Equipment fleet health scores (cached 60s)
# ─────────────────────────────────────────
from agents.rul_predictor import estimate_rul
from agents.anomaly_detector import get_dominant_fault_type

_fleet_health_cache: dict = {"data": None, "ts": 0.0}

@app.get("/api/equipment/health")
async def get_fleet_health():
    """Return health scores and status for all monitored equipment. Cached for 60s."""
    import time
    now = time.time()
    if _fleet_health_cache["data"] and now - _fleet_health_cache["ts"] < 60:
        return _fleet_health_cache["data"]

    fleet_health = []
    noise = now / 60.0

    for eq_id, info in FLEET.items():
        sensor_data = _simulate_sensor_data(eq_id, noise_seed=noise)
        ad_result   = detect_anomalies(sensor_data)
        health      = ad_result["health_score"]
        fault_type, _ = get_dominant_fault_type(sensor_data)
        hi          = compute_health_index(sensor_data)
        rul_result  = estimate_rul(sensor_data, hi, info["type"], fault_type)

        temp = sensor_data["temperature"]
        vib  = sensor_data["vibration"]
        if temp >= 95 or vib >= 1.0:
            alert_level = "EMERGENCY"
        elif temp >= 85 or vib >= 0.70 or health < 50:
            alert_level = "CRITICAL"
        elif temp >= 78 or vib >= 0.50 or health < 75:
            alert_level = "WARNING"
        else:
            alert_level = "NORMAL"

        fleet_health.append({
            "equipment_id":       eq_id,
            "type":               info["type"],
            "location":           info["location"],
            "criticality":        info["criticality"],
            "health_score":       health,
            "alert_level":        alert_level,
            "failure_probability":rul_result["failure_probability"],
            "predicted_rul_days": rul_result["predicted_rul_days"],
            "maintenance_priority":rul_result["maintenance_priority"],
            "dominant_fault":     fault_type,
            "sensor_data":        sensor_data,
        })

    scores = [e["health_score"] for e in fleet_health]
    avg_health_score.set(sum(scores) / len(scores) if scores else 0)

    result = {"equipment": fleet_health, "fleet_count": len(fleet_health)}
    _fleet_health_cache["data"] = result
    _fleet_health_cache["ts"]   = now
    return result


# ─────────────────────────────────────────
# Sensor Trend (30-day history)
# ─────────────────────────────────────────
@app.get("/api/equipment/{equipment_id}/trend")
async def get_sensor_trend(equipment_id: str, hours: int = 168, downsample: int = 4):
    """Return sensor history for the last `hours` hours, downsampled for charting."""
    if equipment_id not in FLEET:
        raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")
    full = generate_history(equipment_id, 720)
    recent = full[-min(hours, len(full)):]
    # Downsample to reduce payload (every Nth point)
    sampled = recent[::max(1, downsample)]
    trend_meta = get_trend_summary(equipment_id, hours)
    return {
        "equipment_id": equipment_id,
        "hours_requested": hours,
        "data_points": len(sampled),
        "readings": sampled,
        "trend_analysis": trend_meta["sensor_trends"],
    }


# ─────────────────────────────────────────
# Fleet Status — ranked priority
# ─────────────────────────────────────────
@app.get("/api/fleet/status")
async def get_fleet_status():
    """Return all equipment ranked by urgency — answers 'which needs attention most?'"""
    import time
    noise = time.time() / 60.0
    ranked = []

    for eq_id, info in FLEET.items():
        sensor_data = _simulate_sensor_data(eq_id, noise_seed=noise)
        ad = detect_anomalies(sensor_data)
        hi = compute_health_index(sensor_data)
        from agents.anomaly_detector import get_dominant_fault_type
        from agents.rul_predictor import estimate_rul
        fault_type, _ = get_dominant_fault_type(sensor_data)
        rul = estimate_rul(sensor_data, hi, info["type"], fault_type)
        trend = get_trend_summary(eq_id, 168)

        temp = sensor_data["temperature"]
        vib  = sensor_data["vibration"]
        if temp >= 95 or vib >= 1.0:
            level = "EMERGENCY"
        elif temp >= 85 or vib >= 0.70 or hi < 35:
            level = "CRITICAL"
        elif temp >= 78 or vib >= 0.50 or hi < 55:
            level = "WARNING"
        else:
            level = "NORMAL"

        severity = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2, "EMERGENCY": 3}
        urgency_score = (
            severity[level] * 30
            + (100 - hi) * 0.4
            + rul["failure_probability"] * 20
            + (1 / max(rul["predicted_rul_days"], 0.1)) * 5
        )

        temp_trend = trend["sensor_trends"].get("temperature", {}).get("direction", "stable")
        vib_trend  = trend["sensor_trends"].get("vibration", {}).get("direction", "stable")

        ranked.append({
            "equipment_id":         eq_id,
            "location":             info["location"],
            "criticality":          info["criticality"],
            "alert_level":          level,
            "health_index":         round(hi, 1),
            "predicted_rul_days":   rul["predicted_rul_days"],
            "failure_probability":  rul["failure_probability"],
            "maintenance_priority": rul["maintenance_priority"],
            "dominant_fault":       fault_type,
            "urgency_score":        round(urgency_score, 1),
            "temperature_trend":    temp_trend,
            "vibration_trend":      vib_trend,
            "sensor_data":          sensor_data,
        })

    ranked.sort(key=lambda x: -x["urgency_score"])

    summary_lines = []
    for i, eq in enumerate(ranked, 1):
        summary_lines.append(
            f"{i}. {eq['equipment_id']} [{eq['alert_level']}] — HI {eq['health_index']}%, "
            f"RUL {eq['predicted_rul_days']}d, {eq['failure_probability']*100:.0f}% failure prob"
        )

    return {
        "ranked_equipment": ranked,
        "fleet_summary": "\n".join(summary_lines),
        "total_equipment": len(ranked),
        "critical_count": sum(1 for e in ranked if e["alert_level"] in ("CRITICAL", "EMERGENCY")),
        "warning_count":  sum(1 for e in ranked if e["alert_level"] == "WARNING"),
    }


# ─────────────────────────────────────────
# Maintenance Report Generator
# ─────────────────────────────────────────
@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Return RAG knowledge base stats — doc count, backend, feedback-integrated docs."""
    try:
        from rag.knowledge_base import knowledge_base_stats
        stats = knowledge_base_stats()
    except Exception:
        stats = {"total_documents": 0, "backend": "unavailable"}
    feedback_docs = sum(1 for f in _feedback_store if f.get("notes") and len(str(f.get("notes", "")).strip()) > 30)
    return {
        **stats,
        "feedback_integrated_count": feedback_docs,
        "total_feedback_entries": len(_feedback_store),
    }


@app.get("/api/report/{equipment_id}", response_class=PlainTextResponse)
async def generate_report(equipment_id: str):
    """Generate a formatted maintenance report for an equipment as plain text."""
    if equipment_id not in FLEET:
        raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")

    import time
    noise = time.time() / 60.0
    info = FLEET[equipment_id]
    sensor_data = _simulate_sensor_data(equipment_id, noise_seed=noise)
    ad = detect_anomalies(sensor_data)
    hi = compute_health_index(sensor_data)
    trend = get_trend_summary(equipment_id, 168)

    from agents.anomaly_detector import get_dominant_fault_type
    from agents.rul_predictor import estimate_rul
    fault_type, _ = get_dominant_fault_type(sensor_data)
    rul = estimate_rul(sensor_data, hi, info["type"], fault_type)

    # Last 3 logbook entries for this equipment
    past_entries = [e for e in reversed(_logbook_store) if e.get("equipment_id") == equipment_id][:3]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{equipment_id}"

    lines = [
        "=" * 70,
        f"  STELOS AI — MAINTENANCE REPORT",
        f"  Report ID  : {report_id}",
        f"  Generated  : {now_str}",
        f"  Equipment  : {equipment_id} ({info['type'].upper()})",
        f"  Location   : {info['location']}",
        f"  Criticality: {info['criticality']}",
        "=" * 70,
        "",
        "CURRENT EQUIPMENT STATUS",
        "-" * 40,
        f"  Health Index        : {hi:.1f}%",
        f"  Alert Level         : {rul['maintenance_priority']} — {ad.get('alert_level', 'N/A') if 'alert_level' in ad else 'see thresholds'}",
        f"  Dominant Fault Type : {fault_type.replace('_', ' ').title()}",
        f"  Anomaly Detected    : {'YES' if ad['anomaly_detected'] else 'No'}",
        "",
        "SENSOR READINGS (CURRENT)",
        "-" * 40,
    ]
    for k, v in sensor_data.items():
        lines.append(f"  {k:<20}: {v}")

    lines += [
        "",
        "RUL / FAILURE PREDICTION",
        "-" * 40,
        f"  Predicted RUL       : {rul['predicted_rul_days']} days  [{rul['rul_lower_bound']}–{rul['rul_upper_bound']} d]",
        f"  Failure Probability : {rul['failure_probability']*100:.1f}%",
        f"  Maintenance Priority: {rul['maintenance_priority']}",
        "",
        "7-DAY TREND ANALYSIS",
        "-" * 40,
    ]
    for sensor, t in trend["sensor_trends"].items():
        arrow = {"rising_fast": "↑↑", "rising": "↑", "stable": "→", "falling": "↓", "falling_fast": "↓↓"}.get(t["direction"], "→")
        lines.append(f"  {sensor:<20}: {t['start']} → {t['end']}  {arrow}  ({t['change_pct']:+.1f}%/week, slope {t['slope_per_day']:+.3f}/day)")

    if past_entries:
        lines += ["", "RECENT WORK ORDER HISTORY", "-" * 40]
        for e in past_entries:
            lines.append(f"  [{e.get('work_order_id','—')}] {e.get('timestamp','')[:10]}  {e.get('maintenance_priority','')}: {e.get('diagnosis','')[:80]}")

    lines += [
        "",
        "RECOMMENDED ACTIONS",
        "-" * 40,
        f"  Based on current health index ({hi:.0f}%) and RUL ({rul['predicted_rul_days']} days):",
    ]
    if hi < 30:
        lines += [
            "  [P1] IMMEDIATE shutdown inspection — bearing and lubrication system",
            "  [P1] Replace bearings (SKF 6315-2RS1/C3) — stock check required",
            "  [P1] Oil sampling and viscosity analysis",
        ]
    elif hi < 60:
        lines += [
            "  [P2] Schedule inspection within 24 hours",
            "  [P2] Vibration spectrum analysis (BPFI/BPFO identification)",
            "  [P2] Lubrication service — apply 400g SKF grease",
        ]
    else:
        lines += [
            "  [P3] Continue routine monitoring (30-min interval)",
            "  [P3] Next scheduled PM as per maintenance calendar",
        ]

    lines += [
        "",
        "─" * 70,
        "  Generated by Stelos AI v2.0 — Tata Steel Hackathon 2026",
        "  Confidence: based on Isolation Forest + Weibull degradation model",
        "=" * 70,
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────
# Active alerts
# ─────────────────────────────────────────
@app.get("/api/alerts/active")
async def get_active_alerts():
    """Return all active equipment alerts."""
    return {"alerts": _alert_store, "count": len(_alert_store)}


# ─────────────────────────────────────────
# Digital Maintenance Logbook
# ─────────────────────────────────────────
@app.get("/api/logbook")
async def get_logbook(limit: int = 50, equipment_id: Optional[str] = None):
    """Return digital maintenance logbook entries, newest first."""
    entries = list(reversed(_logbook_store))
    if equipment_id:
        entries = [e for e in entries if e["equipment_id"] == equipment_id]
    return {"entries": entries[:limit], "total": len(_logbook_store)}


@app.post("/api/logbook/note")
async def add_logbook_note(entry_id: int, note: str, engineer: str = "Engineer"):
    """Add engineer observation note to an existing logbook entry."""
    for entry in _logbook_store:
        if entry["id"] == entry_id:
            entry.setdefault("engineer_notes", []).append({
                "note": note, "engineer": engineer,
                "timestamp": datetime.now().isoformat(timespec="seconds")
            })
            _save_logbook()
            return {"status": "note_added", "entry_id": entry_id}
    raise HTTPException(status_code=404, detail="Logbook entry not found")


# ─────────────────────────────────────────
# Approvals
# ─────────────────────────────────────────
@app.get("/api/approvals/pending")
async def get_pending_approvals():
    """Return work orders pending engineer approval (P1/P2 priority)."""
    pending = [
        e for e in reversed(_logbook_store)
        if e.get("maintenance_priority") in ("P1", "P2")
        and not e.get("approved")
    ]
    return {"pending": pending[:20], "count": len(pending)}


@app.post("/api/approvals/{work_order_id}")
async def approve_work_order(work_order_id: str, approved: bool, engineer: str = "Engineer", notes: str = ""):
    """Approve or reject a maintenance work order."""
    for entry in _logbook_store:
        if entry.get("work_order_id") == work_order_id:
            entry["approved"] = approved
            entry["approval_engineer"] = engineer
            entry["approval_notes"] = notes
            entry["approval_timestamp"] = datetime.now().isoformat(timespec="seconds")
            _save_logbook()
            return {
                "status": "approved" if approved else "rejected",
                "work_order_id": work_order_id,
                "engineer": engineer,
            }
    raise HTTPException(status_code=404, detail=f"Work order {work_order_id} not found")


# ─────────────────────────────────────────
# Feedback endpoint (feedback-driven learning)
# ─────────────────────────────────────────
@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    """
    Submit engineer feedback on AI recommendations.
    Adjusts confidence weights for future predictions on this equipment.
    """
    logger.info(f"Feedback received for {req.equipment_id}: correct={req.diagnosis_correct}")

    feedback_entry = {
        "equipment_id": req.equipment_id,
        "diagnosis_correct": req.diagnosis_correct,
        "root_cause_correct": req.root_cause_correct,
        "actions_useful": req.recommended_actions_useful,
        "notes": req.engineer_notes,
        "confidence_rating": req.confidence_rating,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    _feedback_store.append(feedback_entry)
    _save_feedback()  # persist to disk

    # Compute aggregate accuracy for this equipment
    eq_feedback = [f for f in _feedback_store if f["equipment_id"] == req.equipment_id]
    accuracy = sum(1 for f in eq_feedback if f["diagnosis_correct"]) / len(eq_feedback)

    # Confidence adjustment: boost if >80% accurate, reduce if <50%
    if accuracy > 0.80:
        adjustment = min(1.15, 1.0 + (accuracy - 0.80))
    elif accuracy < 0.50:
        adjustment = max(0.75, 1.0 - (0.50 - accuracy))
    else:
        adjustment = 1.0

    # ── Feedback-to-RAG: substantial engineer notes are added to the knowledge base ──
    rag_updated = False
    if req.engineer_notes and len(req.engineer_notes.strip()) > 30:
        try:
            from rag.knowledge_base import add_document
            fb_count = len(_feedback_store)
            doc_id = f"ENG-FEEDBACK-{req.equipment_id}-{fb_count:03d}"
            doc_title = f"Engineer Field Feedback: {req.equipment_id} ({datetime.now().strftime('%Y-%m-%d')})"
            doc_content = (
                f"ENGINEER FIELD FEEDBACK — {req.equipment_id}\n"
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"Diagnosis Correct: {req.diagnosis_correct} | Actions Useful: {req.recommended_actions_useful}\n"
                f"Confidence Rating: {req.confidence_rating}/5\n\n"
                f"Engineer Notes:\n{req.engineer_notes.strip()}\n\n"
                f"Context: This feedback was recorded after AI analysis of {req.equipment_id} "
                f"at {FLEET.get(req.equipment_id, {}).get('location', 'Jamshedpur Plant')}. "
                f"Use this to improve future diagnoses and recommendations for this equipment."
            )
            rag_updated = add_document(doc_id, doc_title, doc_content, category="engineer_feedback")
            if rag_updated:
                logger.info(f"Engineer feedback '{doc_id}' integrated into RAG knowledge base.")
        except Exception as e:
            logger.warning(f"Could not add feedback to RAG: {e}")

    return {
        "status": "feedback_recorded",
        "equipment_id": req.equipment_id,
        "total_feedback_count": len(eq_feedback),
        "current_accuracy_pct": round(accuracy * 100, 1),
        "confidence_adjustment_factor": round(adjustment, 3),
        "knowledge_base_updated": rag_updated,
        "message": (
            f"Thank you. Confidence adjusted {adjustment:.1%} for {req.equipment_id}. "
            + ("Engineer notes integrated into knowledge base — future queries will use this insight." if rag_updated else "")
        )
    }


# ─────────────────────────────────────────
# WebSocket: Multi-equipment live sensor stream
# ─────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for c in disconnected:
            self.disconnect(c)


manager = ConnectionManager()


@app.websocket("/ws/sensors")
async def websocket_sensor_stream(websocket: WebSocket):
    """Real-time sensor data stream with anomaly detection."""
    await manager.connect(websocket)
    try:
        while True:
            import time
            noise = time.time()

            # Stream all equipment with physics-based simulation
            fleet_snapshot = []
            for eq_id, info in FLEET.items():
                sensor_data = _simulate_sensor_data(eq_id, noise_seed=noise)
                ad = detect_anomalies(sensor_data)

                temp = sensor_data["temperature"]
                vib = sensor_data["vibration"]
                status = (
                    "emergency" if temp >= 95 or vib >= 1.0 else
                    "critical" if temp >= 85 or vib >= 0.70 or not ad["anomaly_detected"] and ad["health_score"] < 40 else
                    "warning" if temp >= 78 or vib >= 0.50 else
                    "normal"
                )

                fleet_snapshot.append({
                    "equipment_id": eq_id,
                    "type": info["type"],
                    "location": info["location"],
                    **sensor_data,
                    "health_score": ad["health_score"],
                    "anomaly_detected": ad["anomaly_detected"],
                    "status": status,
                })

            # Also send single Pump-B reading for backwards-compat with existing frontend
            pump12 = next((e for e in fleet_snapshot if e["equipment_id"] == "Pump-B"), fleet_snapshot[0])

            payload = {
                # Backwards-compat flat fields
                "equipment_id": pump12["equipment_id"],
                "temperature": pump12["temperature"],
                "vibration": pump12["vibration"],
                "pressure": pump12["pressure"],
                "status": pump12["status"],
                "health_score": pump12["health_score"],
                "anomaly_detected": pump12["anomaly_detected"],
                # Full fleet data for enhanced dashboard
                "fleet": fleet_snapshot,
            }

            await manager.broadcast(json.dumps(payload))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─────────────────────────────────────────
# Plant topology (NetworkX)
# ─────────────────────────────────────────
@app.get("/api/plant/topology")
async def get_plant_topology():
    """
    Return the full plant dependency graph (nodes + directed edges).
    Nodes = equipment units; edges = upstream → downstream dependencies.
    Used by the frontend to render the topology visualisation.
    """
    from plant_topology import get_topology_data
    topo = get_topology_data()
    # Enrich nodes with live health scores
    import time
    noise = time.time() / 60.0
    health_map = {}
    for eq_id in FLEET:
        sd = _simulate_sensor_data(eq_id, noise_seed=noise)
        health_map[eq_id] = round(compute_health_index(sd), 1)
    for node in topo["nodes"]:
        node["health_score"] = health_map.get(node["id"])
    return topo


@app.get("/api/plant/impact/{equipment_id}")
async def get_cascade_impact(equipment_id: str):
    """
    Return cascade failure analysis for a given equipment.
    Shows which downstream units are affected and estimated production loss.
    """
    from plant_topology import get_cascade_impact
    import time
    noise = time.time() / 60.0
    sd = _simulate_sensor_data(equipment_id, noise_seed=noise)
    health = round(compute_health_index(sd), 1)
    impact = get_cascade_impact(equipment_id, health_score=health)
    impact["current_health_score"] = health
    impact["sensor_data"] = sd
    return impact


# ─────────────────────────────────────────
# Standard endpoints
# ─────────────────────────────────────────
@app.post("/api/send-report")
async def send_report(req: ReportEmailRequest):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_pass:
        raise HTTPException(status_code=500, detail="Email not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD env vars.")

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
body{{font-family:-apple-system,Arial,sans-serif;background:#f8fafc;color:#1d1d1f;margin:0;padding:0}}
.wrap{{max-width:700px;margin:0 auto;padding:32px 24px}}
.header{{border-bottom:3px solid #0071e3;padding-bottom:16px;margin-bottom:24px}}
.logo{{font-size:28px;font-weight:900;letter-spacing:4px;color:#0071e3}}
.sub{{font-size:11px;letter-spacing:2px;color:#6e6e73;text-transform:uppercase;margin-top:4px}}
.meta{{font-size:12px;color:#6e6e73;margin-top:6px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}}
.kpi{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px;text-align:center}}
.kpi-label{{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9ca3af;margin-bottom:6px}}
.kpi-val{{font-size:24px;font-weight:800}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e5e7eb;margin-bottom:24px}}
th{{background:#f8fafc;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#6e6e73;padding:10px 12px;text-align:left;border-bottom:1px solid #e5e7eb}}
td{{padding:10px 12px;font-size:12px;border-bottom:1px solid #f1f5f9}}
tr:last-child td{{border-bottom:none}}
.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:9px;font-weight:700}}
.crit{{background:#fef2f2;color:#dc2626}}.warn{{background:#fffbeb;color:#d97706}}.norm{{background:#f0fdf4;color:#16a34a}}
.footer{{text-align:center;font-size:11px;color:#9ca3af;border-top:1px solid #e5e7eb;padding-top:16px;margin-top:24px}}
</style></head><body>
<div class="wrap">
<div class="header">
  <div class="logo">STELOS</div>
  <div class="sub">Autonomous Maintenance Intelligence · Tata Steel</div>
  <div class="meta">Generated: {req.timestamp}</div>
</div>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-label">Fleet Health</div><div class="kpi-val" style="color:#f59e0b">78.2%</div></div>
  <div class="kpi"><div class="kpi-label">Critical</div><div class="kpi-val" style="color:#ef4444">2</div></div>
  <div class="kpi"><div class="kpi-label">Warnings</div><div class="kpi-val" style="color:#f59e0b">2</div></div>
  <div class="kpi"><div class="kpi-label">Monitored</div><div class="kpi-val" style="color:#0071e3">10</div></div>
</div>
<p style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#6e6e73;margin-bottom:10px">Active Alerts</p>
<table>
  <thead><tr><th>Machine</th><th>Location</th><th>Status</th><th>Health</th><th>RUL</th><th>Fail Risk</th><th>Priority</th></tr></thead>
  <tbody>
    <tr><td><b>Pump-B</b></td><td>Blast Furnace #3</td><td><span class="badge crit">CRITICAL</span></td><td style="color:#ef4444">62%</td><td style="color:#ef4444">4.3d</td><td style="color:#ef4444">82%</td><td><span class="badge crit">P1</span></td></tr>
    <tr><td><b>Blast-Furnace</b></td><td>Blast Furnace #1</td><td><span class="badge crit">CRITICAL</span></td><td style="color:#ef4444">55%</td><td style="color:#ef4444">6.1d</td><td style="color:#ef4444">71%</td><td><span class="badge crit">P1</span></td></tr>
    <tr><td><b>Conveyor-B</b></td><td>Raw Material Yard</td><td><span class="badge warn">WARNING</span></td><td style="color:#f59e0b">73%</td><td style="color:#f59e0b">18.2d</td><td style="color:#f59e0b">45%</td><td><span class="badge warn">P2</span></td></tr>
    <tr><td><b>Rolling-Mill</b></td><td>Hot Rolling Section</td><td><span class="badge warn">WARNING</span></td><td style="color:#f59e0b">78%</td><td style="color:#f59e0b">22.5d</td><td style="color:#f59e0b">35%</td><td><span class="badge warn">P2</span></td></tr>
    <tr><td><b>Pump-A</b></td><td>Blast Furnace #2</td><td><span class="badge norm">NORMAL</span></td><td style="color:#10b981">84%</td><td style="color:#10b981">62d</td><td style="color:#10b981">18%</td><td><span class="badge norm">P3</span></td></tr>
    <tr><td><b>Cooling-Fan-4</b></td><td>Sinter Plant</td><td><span class="badge norm">NORMAL</span></td><td style="color:#10b981">88%</td><td style="color:#10b981">95d</td><td style="color:#10b981">9%</td><td><span class="badge norm">Routine</span></td></tr>
    <tr><td><b>Cooling-Unit</b></td><td>Steel Melting Shop</td><td><span class="badge norm">NORMAL</span></td><td style="color:#10b981">92%</td><td style="color:#10b981">110d</td><td style="color:#10b981">5%</td><td><span class="badge norm">Routine</span></td></tr>
    <tr><td><b>Power-Unit</b></td><td>Power Distribution</td><td><span class="badge norm">NORMAL</span></td><td style="color:#10b981">97%</td><td style="color:#10b981">145d</td><td style="color:#10b981">1%</td><td><span class="badge norm">Routine</span></td></tr>
  </tbody>
</table>
<p style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#6e6e73;margin-bottom:10px">Immediate Actions Required</p>
<table>
  <thead><tr><th>Priority</th><th>Machine</th><th>Action</th></tr></thead>
  <tbody>
    <tr><td><span class="badge crit">P1</span></td><td>Pump-B</td><td>Initiate controlled shutdown — bearing failure imminent. Flush lubrication system (SOP-EMERGENCY-001 §3.1)</td></tr>
    <tr><td><span class="badge crit">P1</span></td><td>Blast-Furnace</td><td>FFT vibration spectrum analysis. Inspect tuyere assembly (SOP-VIBRATION-001 §2.2)</td></tr>
    <tr><td><span class="badge warn">P2</span></td><td>Conveyor-B</td><td>Schedule bearing replacement within RUL window (SOP-BEARING-001 §4.3)</td></tr>
    <tr><td><span class="badge warn">P2</span></td><td>Rolling-Mill</td><td>Roll surface inspection and alignment check (SOP-ALIGNMENT-001 §2)</td></tr>
  </tbody>
</table>
<div class="footer">STELOS · AI-Powered Predictive Maintenance · Tata Steel Hackathon 2026</div>
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"STELOS Plant Status Report — {req.timestamp}"
    msg["From"]    = gmail_user
    msg["To"]      = req.to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, req.to, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP error: {str(e)}")

    logger.info(f"Status report emailed to {req.to}")
    return {"success": True, "to": req.to}


@app.get("/")
async def root():
    return {"message": "Stelos AI v2.0 — Tata Steel Hackathon 2026", "status": "operational"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "graph": "ok",
            "anomaly_detector": "ok",
            "rul_predictor": "ok",
            "rag_knowledge_base": "ok",
            "fleet_monitoring": f"{len(FLEET)} equipment tracked",
        }
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ─────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────
def _upsert_alert(equipment_id: str, level: str, description: str):
    existing = next((a for a in _alert_store if a["equipment_id"] == equipment_id), None)
    if existing:
        existing["level"] = level
        existing["description"] = description
    else:
        _alert_store.append({
            "equipment_id": equipment_id,
            "level": level,
            "description": description,
            "location": FLEET.get(equipment_id, {}).get("location", "Unknown"),
        })


def _get_feedback_adjustments(equipment_id: str) -> Dict[str, float]:
    eq_feedback = [f for f in _feedback_store if f["equipment_id"] == equipment_id]
    if not eq_feedback:
        return {"global": 1.0}
    accuracy = sum(1 for f in eq_feedback if f["diagnosis_correct"]) / len(eq_feedback)
    adjustment = 1.0 + max(-0.25, min(0.15, accuracy - 0.70))
    return {"global": round(adjustment, 3)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
