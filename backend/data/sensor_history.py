"""
30-day synthetic sensor history generator.
Deterministic per equipment_id — same seed every restart so trends look consistent.
Pump-12 and Conveyor-B show degradation curves; others are stable.
"""
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List

_cache: Dict[str, List] = {}

PROFILES = {
    "Pump-12":       {"temp": 70.0, "vib": 0.40, "degrading": True,  "speed": 1.8},
    "Pump-11":       {"temp": 64.0, "vib": 0.27, "degrading": False, "speed": 0.3},
    "Pump-13":       {"temp": 62.0, "vib": 0.24, "degrading": False, "speed": 0.2},
    "Conveyor-B":    {"temp": 66.0, "vib": 0.36, "degrading": True,  "speed": 0.9},
    "Cooling-Fan-4": {"temp": 61.0, "vib": 0.24, "degrading": False, "speed": 0.2},
}


def generate_history(equipment_id: str, hours: int = 720) -> List[Dict]:
    """Return cached hourly readings for the last `hours` hours (default 30 days)."""
    key = f"{equipment_id}_{hours}"
    if key in _cache:
        return _cache[key]

    p = PROFILES.get(equipment_id, {"temp": 65.0, "vib": 0.30, "degrading": False, "speed": 0.3})
    rng = random.Random(abs(hash(equipment_id)) % (2 ** 31))
    now = datetime.now(timezone.utc)
    history = []

    for i in range(hours, 0, -1):
        ts = now - timedelta(hours=i)
        progress = (hours - i) / hours          # 0.0 → 1.0

        deg = (progress ** 2) * p["speed"] if p["degrading"] else 0.0
        diurnal = 2.5 * math.sin((ts.hour - 6) * math.pi / 12)

        history.append({
            "timestamp":     ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "temperature":   round(p["temp"] + deg * 22 + diurnal + rng.uniform(-1.5, 1.5), 1),
            "vibration":     round(max(0.05, p["vib"] + deg * 0.33 + rng.uniform(-0.015, 0.015)), 3),
            "pressure":      round(100.0 - deg * 16 + rng.uniform(-2, 2), 1),
            "oil_temp":      round(52.0 + deg * 17 + rng.uniform(-1, 1), 1),
            "motor_current": round(13.5 + deg * 5 + rng.uniform(-0.3, 0.3), 1),
        })

    _cache[key] = history
    return history


def get_trend_summary(equipment_id: str, hours: int = 168) -> Dict:
    """Linear-regression slope + stats for each sensor over the last `hours` hours."""
    full = generate_history(equipment_id, 720)
    recent = full[-min(hours, len(full)):]

    sensors = ["temperature", "vibration", "pressure", "oil_temp", "motor_current"]
    trends = {}
    n = len(recent)

    for s in sensors:
        vals = [r[s] for r in recent]
        x_mean = (n - 1) / 2
        y_mean = sum(vals) / n
        num = sum((i - x_mean) * (vals[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = (num / den) if den else 0
        slope_per_day = slope * 24

        if slope_per_day > 0.8:
            direction = "rising_fast"
        elif slope_per_day > 0.15:
            direction = "rising"
        elif slope_per_day < -0.8:
            direction = "falling_fast"
        elif slope_per_day < -0.15:
            direction = "falling"
        else:
            direction = "stable"

        trends[s] = {
            "start":          round(vals[0], 2),
            "end":            round(vals[-1], 2),
            "min":            round(min(vals), 2),
            "max":            round(max(vals), 2),
            "mean":           round(y_mean, 2),
            "slope_per_day":  round(slope_per_day, 3),
            "direction":      direction,
            "change_pct":     round((vals[-1] - vals[0]) / max(abs(vals[0]), 0.001) * 100, 1),
        }

    return {
        "equipment_id":   equipment_id,
        "hours_analyzed": hours,
        "sensor_trends":  trends,
    }
