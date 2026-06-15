"""
Isolation Forest-based multi-sensor anomaly detection for steel plant equipment.
Pre-trained on synthetic nominal operating data representing normal plant conditions.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("Stelos.AnomalyDetector")

# ─────────────────────────────────────────
# Normal operating envelopes (Jamshedpur blast furnace pumps)
# ─────────────────────────────────────────
SENSOR_SPECS = {
    "temperature": {"nominal": 65.0, "std": 8.0, "min": 50.0, "max": 80.0, "unit": "°C", "alarm": 85.0, "trip": 95.0},
    "vibration":   {"nominal": 0.30, "std": 0.08, "min": 0.10, "max": 0.50, "unit": "mm/s", "alarm": 0.70, "trip": 1.0},
    "pressure":    {"nominal": 100.0, "std": 5.0,  "min": 90.0, "max": 110.0, "unit": "PSI", "alarm_low": 80.0, "alarm_high": 120.0},
    "motor_current": {"nominal": 42.0, "std": 3.0,  "min": 35.0, "max": 50.0, "unit": "A", "alarm": 55.0},
    "oil_temp":    {"nominal": 52.0, "std": 5.0,  "min": 45.0, "max": 65.0, "unit": "°C", "alarm": 70.0},
}

SENSOR_FEATURE_ORDER = ["temperature", "vibration", "pressure", "motor_current", "oil_temp"]


def _generate_training_data(n_normal: int = 2000) -> np.ndarray:
    """Generate synthetic normal operating data for Isolation Forest training."""
    np.random.seed(42)
    rows = []
    for _ in range(n_normal):
        row = []
        for sensor in SENSOR_FEATURE_ORDER:
            spec = SENSOR_SPECS[sensor]
            # Truncated normal within min/max bounds
            val = np.clip(
                np.random.normal(spec["nominal"], spec["std"]),
                spec["min"], spec["max"]
            )
            row.append(val)
        rows.append(row)

    # Add a small fraction of borderline anomalies so the model learns boundaries
    for _ in range(100):
        row = []
        for sensor in SENSOR_FEATURE_ORDER:
            spec = SENSOR_SPECS[sensor]
            # Slightly outside normal but not catastrophic
            val = np.random.normal(spec["nominal"] + spec["std"] * 2, spec["std"])
            row.append(val)
        rows.append(row)

    return np.array(rows)


# ─────────────────────────────────────────
# Module-level singleton: train once on import
# ─────────────────────────────────────────
_scaler = StandardScaler()
_iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.05,   # ~5% anomaly rate expected in industrial data
    max_samples="auto",
    random_state=42,
    n_jobs=-1
)

_training_data = _generate_training_data()
_scaler.fit(_training_data)
_iso_forest.fit(_scaler.transform(_training_data))

logger.info("Isolation Forest trained on %d normal operating samples.", len(_training_data))


def detect_anomalies(sensor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Isolation Forest anomaly detection on incoming sensor readings.

    Parameters
    ----------
    sensor_data : dict with keys like 'temperature', 'vibration', 'pressure', etc.

    Returns
    -------
    dict with:
        anomaly_detected : bool
        overall_anomaly_score : float  (positive = normal, negative = anomaly, range -1 to 1)
        per_sensor_scores : dict[sensor -> score]
        anomaly_details : list of human-readable descriptions
        health_score : float (0-100)
    """
    # Extract features with fallback to nominal values
    feature_vector = []
    for sensor in SENSOR_FEATURE_ORDER:
        nominal = SENSOR_SPECS[sensor]["nominal"]
        val = float(sensor_data.get(sensor, nominal))
        feature_vector.append(val)

    X = np.array(feature_vector).reshape(1, -1)
    X_scaled = _scaler.transform(X)

    # Isolation Forest score: negative = anomaly, positive = normal
    overall_score = float(_iso_forest.score_samples(X_scaled)[0])
    is_anomaly = _iso_forest.predict(X_scaled)[0] == -1

    # Per-sensor anomaly scoring via z-score (deviation from nominal)
    per_sensor: Dict[str, float] = {}
    anomaly_details: List[str] = []

    for i, sensor in enumerate(SENSOR_FEATURE_ORDER):
        spec = SENSOR_SPECS[sensor]
        val = feature_vector[i]
        z = abs(val - spec["nominal"]) / spec["std"]
        per_sensor[sensor] = round(z, 2)

        # Generate human-readable detail for significant deviations
        if sensor == "temperature" and val > spec["alarm"]:
            anomaly_details.append(
                f"Bearing temperature {val:.1f}{spec['unit']} exceeds alarm threshold {spec['alarm']}{spec['unit']} "
                f"(+{val - spec['nominal']:.1f} above nominal)"
            )
        elif sensor == "temperature" and val > spec["max"]:
            anomaly_details.append(
                f"Bearing temperature {val:.1f}{spec['unit']} outside normal operating range [{spec['min']}-{spec['max']}]{spec['unit']}"
            )
        elif sensor == "vibration" and val > spec["alarm"]:
            anomaly_details.append(
                f"Vibration velocity {val:.3f}{spec['unit']} exceeds ISO 10816-3 alarm limit {spec['alarm']}{spec['unit']}"
            )
        elif sensor == "vibration" and val > spec["max"]:
            anomaly_details.append(
                f"Vibration velocity {val:.3f}{spec['unit']} in Zone C (unsatisfactory for long-term operation)"
            )
        elif sensor == "pressure":
            if val < spec.get("alarm_low", 0):
                anomaly_details.append(
                    f"Discharge pressure {val:.1f}{spec['unit']} below alarm low threshold {spec.get('alarm_low')}{spec['unit']}"
                )
            elif val > spec.get("alarm_high", 9999):
                anomaly_details.append(
                    f"Discharge pressure {val:.1f}{spec['unit']} exceeds alarm high threshold {spec.get('alarm_high')}{spec['unit']}"
                )
        elif sensor == "motor_current" and val > spec.get("alarm", 9999):
            anomaly_details.append(
                f"Motor current {val:.1f}{spec['unit']} exceeds alarm threshold {spec['alarm']}{spec['unit']} — possible rotor issue"
            )
        elif sensor == "oil_temp" and val > spec.get("alarm", 9999):
            anomaly_details.append(
                f"Lubrication oil temperature {val:.1f}{spec['unit']} elevated above {spec['alarm']}{spec['unit']} — lubrication degradation risk"
            )
        elif z > 2.5:
            anomaly_details.append(
                f"{sensor.replace('_', ' ').title()} showing {z:.1f}σ deviation from nominal — abnormal reading"
            )

    if not anomaly_details and is_anomaly:
        anomaly_details.append(
            "Multi-sensor pattern deviates from normal operating profile (Isolation Forest flag)"
        )

    # Health score: weighted composite of sensor health
    sensor_weights = {"temperature": 0.35, "vibration": 0.30, "pressure": 0.15, "motor_current": 0.10, "oil_temp": 0.10}
    health_score = 100.0
    for i, sensor in enumerate(SENSOR_FEATURE_ORDER):
        spec = SENSOR_SPECS[sensor]
        val = feature_vector[i]
        w = sensor_weights.get(sensor, 0.1)

        # Normalize degradation from nominal range
        range_half = (spec["max"] - spec["min"]) / 2.0
        deviation = abs(val - spec["nominal"]) / max(range_half, 1e-6)
        degradation = min(deviation * 50.0, 50.0)  # max 50 points deducted per sensor
        health_score -= w * degradation

    health_score = round(max(0.0, min(100.0, health_score)), 1)

    return {
        "anomaly_detected": bool(is_anomaly),
        "overall_anomaly_score": round(overall_score, 4),
        "per_sensor_scores": per_sensor,
        "anomaly_details": anomaly_details,
        "health_score": health_score,
        "sensor_readings": {
            s: {"value": feature_vector[i], "unit": SENSOR_SPECS[s]["unit"],
                "nominal": SENSOR_SPECS[s]["nominal"], "z_score": per_sensor[s]}
            for i, s in enumerate(SENSOR_FEATURE_ORDER)
        }
    }


def get_dominant_fault_type(sensor_data: Dict[str, Any]) -> Tuple[str, float]:
    """
    Determine the dominant fault type from sensor readings.
    Returns (fault_type, confidence).
    """
    temp = float(sensor_data.get("temperature", SENSOR_SPECS["temperature"]["nominal"]))
    vib = float(sensor_data.get("vibration", SENSOR_SPECS["vibration"]["nominal"]))
    pressure = float(sensor_data.get("pressure", SENSOR_SPECS["pressure"]["nominal"]))
    oil_temp = float(sensor_data.get("oil_temp", SENSOR_SPECS["oil_temp"]["nominal"]))
    current = float(sensor_data.get("motor_current", SENSOR_SPECS["motor_current"]["nominal"]))

    scores: Dict[str, float] = {}

    # Overheating / lubrication failure
    temp_dev = (temp - SENSOR_SPECS["temperature"]["nominal"]) / SENSOR_SPECS["temperature"]["std"]
    oil_dev = (oil_temp - SENSOR_SPECS["oil_temp"]["nominal"]) / SENSOR_SPECS["oil_temp"]["std"]
    scores["lubrication_failure"] = max(0, (temp_dev * 0.6 + oil_dev * 0.4))

    # Bearing wear / mechanical degradation
    vib_dev = (vib - SENSOR_SPECS["vibration"]["nominal"]) / SENSOR_SPECS["vibration"]["std"]
    scores["bearing_wear"] = max(0, vib_dev)

    # Impeller / hydraulic issue
    pressure_dev = (SENSOR_SPECS["pressure"]["nominal"] - pressure) / SENSOR_SPECS["pressure"]["std"]  # low pressure is bad
    scores["impeller_wear"] = max(0, pressure_dev)

    # Electrical / motor issue
    current_dev = (current - SENSOR_SPECS["motor_current"]["nominal"]) / SENSOR_SPECS["motor_current"]["std"]
    scores["motor_fault"] = max(0, current_dev)

    if not scores or max(scores.values()) <= 0:
        return "normal_operation", 0.95

    best_fault = max(scores, key=lambda k: scores[k])
    raw_score = scores[best_fault]
    confidence = round(min(0.95, 0.40 + raw_score * 0.15), 2)

    return best_fault, confidence
