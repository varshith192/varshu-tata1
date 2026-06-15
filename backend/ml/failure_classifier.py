"""
XGBoost failure classifier trained on AI4I 2020 Predictive Maintenance Dataset.
Provides per-prediction SHAP values for explainable AI (XAI).

Training happens once at startup and is cached to disk.
Inference + SHAP on a single sample: < 50ms.
"""
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger("Stelos.ML")

_CACHE_PATH = Path(__file__).parent / "_model_cache" / "xgb_classifier.pkl"

FEATURE_NAMES = [
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
    "temp_diff",
    "power",
    "rpm_torque_ratio",
]

FAILURE_TYPE_LABELS = {
    "TWF": "Tool Wear Failure",
    "HDF": "Heat Dissipation Failure",
    "PWF": "Power Failure",
    "OSF": "Overstrain Failure",
    "NONE": "No Failure Detected",
}

_cache: Dict[str, Any] = {}


def _sensor_to_features(sensor_data: Dict[str, float], health_score: float) -> np.ndarray:
    """Map equipment sensor readings into AI4I 2020 feature space."""
    temp          = float(sensor_data.get("temperature",   70.0))
    oil_temp      = float(sensor_data.get("oil_temp",      55.0))
    motor_current = float(sensor_data.get("motor_current", 14.0))
    vibration     = float(sensor_data.get("vibration",     0.30))

    air_temperature    = temp + 230.0                                    # ~300 K nominal
    process_temperature = oil_temp + 255.0                               # ~310 K nominal
    rotational_speed   = int(np.clip(motor_current * 95 + 200, 800, 3000))
    torque             = float(np.clip(vibration * 55 + 15, 3.0, 80.0))
    tool_wear          = int(np.clip((1.0 - health_score / 100.0) * 250, 0, 250))

    temp_diff        = process_temperature - air_temperature
    power            = torque * rotational_speed * 2.0 * np.pi / 60.0
    rpm_torque_ratio = rotational_speed / max(torque, 0.1)

    return np.array([[
        air_temperature,
        process_temperature,
        rotational_speed,
        torque,
        tool_wear,
        temp_diff,
        power,
        rpm_torque_ratio,
    ]], dtype=np.float32)


def _train_and_cache() -> Dict[str, Any]:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score

    from .ai4i_data import generate

    logger.info("Training XGBoost on AI4I 2020 dataset (10,000 samples)…")
    df = generate(10000, seed=42)

    X = df[FEATURE_NAMES].values.astype(np.float32)
    y = df["machine_failure"].values

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    pos_weight = float((y_tr == 0).sum()) / max(float((y_tr == 1).sum()), 1)

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.80,
        colsample_bytree=0.80,
        scale_pos_weight=pos_weight,
        random_state=42,
        eval_metric="logloss",
        verbosity=0,
    )
    model.fit(X_tr, y_tr)

    y_prob = model.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, y_prob)
    logger.info(f"XGBoost AUC-ROC on test set: {auc:.4f}")

    # Per-failure-type classifiers
    type_models: Dict[str, Any] = {}
    for ft in ["TWF", "HDF", "PWF", "OSF"]:
        yt = df[ft].values
        if yt.sum() < 5:
            continue
        Xt, _, yt_tr, _ = train_test_split(X, yt, test_size=0.20, random_state=42)
        pw = float((yt_tr == 0).sum()) / max(float((yt_tr == 1).sum()), 1)
        m = xgb.XGBClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.10,
            scale_pos_weight=pw, random_state=42, verbosity=0,
        )
        m.fit(Xt, yt_tr)
        type_models[ft] = m

    payload = {
        "model":         model,
        "type_models":   type_models,
        "auc":           auc,
        "feature_names": FEATURE_NAMES,
    }

    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CACHE_PATH, "wb") as fh:
        pickle.dump(payload, fh)
    logger.info(f"Model saved → {_CACHE_PATH}")
    return payload


def _get_cache() -> Dict[str, Any]:
    if _cache:
        return _cache

    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, "rb") as fh:
                data = pickle.load(fh)
            _cache.update(data)
            logger.info(f"Loaded XGBoost model (AUC={data.get('auc', 0):.4f})")
            return _cache
        except Exception as exc:
            logger.warning(f"Cache load failed ({exc}), retraining…")

    data = _train_and_cache()
    _cache.update(data)
    return _cache


def _xgb_shap(model: Any, features: np.ndarray) -> List[float]:
    """
    Compute TreeSHAP values using XGBoost's built-in implementation.
    No external shap library required — XGBoost 2.0+ has TreeSHAP natively.
    pred_contribs returns shape (n_samples, n_features + 1); last col is bias.
    """
    import xgboost as xgb
    dmatrix = xgb.DMatrix(features, feature_names=FEATURE_NAMES)
    contribs = model.get_booster().predict(dmatrix, pred_contribs=True)
    return contribs[0, :-1].tolist()   # drop bias term


def predict(sensor_data: Dict[str, float], health_score: float = 80.0) -> Dict[str, Any]:
    """
    Returns:
        ml_failure_probability  – float 0-1 from XGBoost
        predicted_failure_type  – "TWF" | "HDF" | "PWF" | "OSF" | "NONE"
        failure_type_label      – human-readable string
        failure_type_probs      – per-type probabilities
        shap_values             – {feature: shap_value}
        shap_top_features       – top-6 list for the waterfall chart
        model_auc               – float (test-set AUC)
    """
    try:
        cache       = _get_cache()
        model       = cache["model"]
        type_models = cache["type_models"]
        auc         = cache.get("auc", 0.0)

        features = _sensor_to_features(sensor_data, health_score)

        ml_prob = float(model.predict_proba(features)[0, 1])

        # Which failure type is most likely?
        type_probs: Dict[str, float] = {}
        for ft, m in type_models.items():
            type_probs[ft] = float(m.predict_proba(features)[0, 1])

        best_type = max(type_probs, key=type_probs.get) if type_probs else "NONE"
        if not type_probs or type_probs[best_type] < 0.12:
            best_type = "NONE"

        # TreeSHAP via XGBoost's native implementation (no shap library needed)
        sv_flat = _xgb_shap(model, features)
        shap_dict = {
            FEATURE_NAMES[i]: round(float(sv_flat[i]), 4)
            for i in range(len(FEATURE_NAMES))
        }
        shap_sorted: List[Dict[str, Any]] = sorted(
            [{"feature": k, "shap": v} for k, v in shap_dict.items()],
            key=lambda x: abs(x["shap"]),
            reverse=True,
        )

        return {
            "ml_failure_probability":  round(ml_prob, 4),
            "predicted_failure_type":  best_type,
            "failure_type_label":      FAILURE_TYPE_LABELS.get(best_type, best_type),
            "failure_type_probs":      {k: round(v, 3) for k, v in type_probs.items()},
            "shap_values":             shap_dict,
            "shap_top_features":       shap_sorted[:6],
            "model_auc":               round(auc, 4),
        }

    except Exception as exc:
        logger.error(f"ML predict failed: {exc}", exc_info=True)
        return {
            "ml_failure_probability":  0.0,
            "predicted_failure_type":  "NONE",
            "failure_type_label":      "No Failure Detected",
            "failure_type_probs":      {},
            "shap_values":             {},
            "shap_top_features":       [],
            "model_auc":               0.0,
        }


def warmup() -> None:
    """Call at startup so the first user request isn't slow."""
    try:
        _get_cache()
    except Exception as exc:
        logger.warning(f"ML warmup failed (xgboost/shap not installed?): {exc}")
