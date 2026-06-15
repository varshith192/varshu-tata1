"""
Stelos AI — 6-Agent Node Implementations
Pipeline: Diagnostic → KnowledgeRetrieval → RootCause → PredictiveMaintenance → BusinessImpact → ExecutiveIntelligence

Agentic design: LLMs are the decision-makers. ML models (Isolation Forest, Weibull) are tools
that feed data INTO the LLM — the LLM reasons and decides, not hardcoded if/elif chains.
"""
import os
import logging
from typing import Any, Dict, List

from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from .state import MaintenanceState
from .anomaly_detector import detect_anomalies, get_dominant_fault_type
from .rul_predictor import compute_health_index, estimate_rul
from rag.knowledge_base import retrieve, retrieve_for_fault

logger = logging.getLogger("Stelos.Agents")


def _get_fast_llm(temperature: float = 0.1, max_tokens: int = 250):
    """Agents 1, 3, 4 — 3s timeout so slow Groq fails fast and rule-based kicks in."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and groq_key != "your_groq_api_key_here":
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=groq_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=3,
                max_retries=0,
            )
        except Exception as e:
            logger.warning(f"Groq fast-model init failed: {e}")

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=gemini_key,
                temperature=temperature,
                max_output_tokens=max_tokens,
                timeout=3,
                max_retries=0,
            )
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")
    return None


def _get_llm(temperature: float = 0.2):
    """Agent 6 — 5s timeout; if Groq is fast it answers, if slow rule-based fallback fires."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and groq_key != "your_groq_api_key_here":
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=groq_key,
                temperature=temperature,
                max_tokens=400,
                timeout=5,
                max_retries=0,
            )
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=gemini_key,
                temperature=temperature,
                max_output_tokens=400,
                timeout=5,
                max_retries=0,
            )
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    return None


def _append_trace(state: MaintenanceState, trace: dict):
    traces = state.get("agent_traces", [])
    traces.append(trace)
    return traces


# ─────────────────────────────────────────
# Structured output schemas — LLM must return these exact shapes
# ─────────────────────────────────────────

class DiagnosisOutput(BaseModel):
    alert_level: str = Field(
        description="Severity: EMERGENCY (shutdown risk), CRITICAL (failure imminent), WARNING (degrading), NORMAL (healthy)"
    )
    diagnosis: str = Field(
        description="One sentence describing the equipment condition and primary fault signal"
    )
    reasoning: str = Field(
        description="Technical justification referencing specific sensor scores and health index"
    )


class WorkOrderItem(BaseModel):
    action: str = Field(description="Specific maintenance action the technician must take")
    priority: str = Field(description="P1 (immediate), P2 (24h), P3 (this week), or Routine")
    sop_reference: str = Field(description="SOP section reference e.g. SOP-PUMP-001 §2.1")
    estimated_time: str = Field(description="Time to complete e.g. '2 hours'")
    type: str = Field(description="corrective, diagnostic, replacement, monitoring, or routine")


class MaintenancePlan(BaseModel):
    risk_level: str = Field(description="Critical, High, Medium, or Low")
    risk_reasoning: str = Field(
        description="One sentence explaining risk level based on RUL, failure probability, and equipment criticality"
    )
    recommended_actions: List[WorkOrderItem] = Field(
        description="3 to 6 prioritized work orders derived from the retrieved SOPs and failure reports"
    )


# ─────────────────────────────────────────
# 1. DIAGNOSTIC AGENT
#    Tool: Isolation Forest (ML) → gives anomaly scores + health index
#    Decision-maker: LLM interprets those scores and classifies severity
#    No hardcoded temperature/vibration thresholds — LLM reasons about the data
# ─────────────────────────────────────────
def diagnostic_agent(state: MaintenanceState) -> Dict[str, Any]:
    sensor_data = state.get("sensor_data", {})
    equipment_id = state.get("equipment_id", "Unknown")

    # ── Tool 1: Isolation Forest ──
    ad_result = detect_anomalies(sensor_data)
    health_score = ad_result["health_score"]
    anomaly_detected = ad_result["anomaly_detected"]
    anomaly_details = ad_result["anomaly_details"]
    per_sensor_scores = ad_result["per_sensor_scores"]

    # ── Tool 2: XGBoost + SHAP (trained on AI4I 2020 dataset) ──
    ml_result: Dict[str, Any] = {}
    try:
        from ml.failure_classifier import predict as ml_predict
        ml_result = ml_predict(sensor_data, health_score)
        logger.info(
            f"XGBoost: failure_prob={ml_result['ml_failure_probability']:.3f} "
            f"type={ml_result['predicted_failure_type']} "
            f"AUC={ml_result['model_auc']:.4f}"
        )
    except Exception as exc:
        logger.warning(f"XGBoost/SHAP unavailable: {exc}")

    ml_prob      = ml_result.get("ml_failure_probability", 0.0)
    failure_type = ml_result.get("predicted_failure_type", "NONE")
    failure_label = ml_result.get("failure_type_label", "No Failure Detected")
    shap_values  = ml_result.get("shap_values", {})
    shap_top     = ml_result.get("shap_top_features", [])
    model_auc    = ml_result.get("model_auc", 0.0)

    # ── LLM Decision: classify severity from both ML tool outputs ──
    alert_level = "NORMAL"
    diagnosis = f"Normal Operation — {equipment_id} sensors within nominal envelope."
    llm_reasoning = "No LLM available — rule-based fallback used."

    # Fast path: skip LLM for clearly normal equipment (health > 75, prob < 0.20)
    _skip_llm = health_score > 75 and ml_prob < 0.20 and not anomaly_detected

    llm = None if _skip_llm else _get_fast_llm(temperature=0.1, max_tokens=150)
    if llm:
        try:
            structured_llm = llm.with_structured_output(DiagnosisOutput)
            shap_summary = ", ".join(f"{s['feature']}={s['shap']:+.3f}" for s in shap_top[:4]) if shap_top else "N/A"

            prompt = f"""Tata Steel Reliability Engineer. Classify alert level for {equipment_id}.

Isolation Forest: Health={health_score:.0f}/100, Anomaly={anomaly_detected}, Details={anomaly_details[:2]}
XGBoost (AI4I 2020, AUC={model_auc:.3f}): Prob={ml_prob:.0%}, Type={failure_label}, SHAP={shap_summary}
Sensors: Temp={sensor_data.get('temperature')}°C Vib={sensor_data.get('vibration')} Oil={sensor_data.get('oil_temp')}°C Current={sensor_data.get('motor_current')}A

Alert rules: EMERGENCY=Health<20 or Prob>0.85 | CRITICAL=Health<45 or Prob>0.60 | WARNING=Health<65 or Prob>0.30 | NORMAL=rest
Write diagnosis as one technical sentence referencing the dominant sensor signal."""

            result = structured_llm.invoke(prompt)
            alert_level = result.alert_level.upper()
            if alert_level not in ("EMERGENCY", "CRITICAL", "WARNING", "NORMAL"):
                alert_level = "NORMAL"
            diagnosis = result.diagnosis
            llm_reasoning = result.reasoning
        except Exception as e:
            logger.warning(f"LLM diagnosis failed: {e} — using rule-based fallback")
            # Fallback: derive from health score and anomaly flag
            if health_score < 20 or ad_result["overall_anomaly_score"] < -0.5:
                alert_level = "EMERGENCY"
            elif health_score < 45 or (anomaly_detected and health_score < 55):
                alert_level = "CRITICAL"
            elif health_score < 65 or anomaly_detected:
                alert_level = "WARNING"
            else:
                alert_level = "NORMAL"
            if alert_level == "NORMAL" and health_score >= 80:
                diagnosis = f"Normal Operation — {equipment_id} sensors within nominal envelope. Health {health_score:.0f}%."
            elif anomaly_details:
                diagnosis = f"Anomaly Detected on {equipment_id}: {anomaly_details[0]}"
            else:
                diagnosis = f"Normal Operation — {equipment_id} all sensors within nominal envelope."
            llm_reasoning = f"Fallback: health_score={health_score:.1f}, anomaly={anomaly_detected}"
    else:
        # No LLM — derive from Isolation Forest health score alone
        if health_score < 20:
            alert_level = "EMERGENCY"
        elif health_score < 45:
            alert_level = "CRITICAL"
        elif health_score < 65 or anomaly_detected:
            alert_level = "WARNING"
        if alert_level == "NORMAL" and health_score >= 80:
            diagnosis = f"Normal Operation — {equipment_id} sensors within nominal envelope. Health {health_score:.0f}%."
        elif anomaly_details:
            diagnosis = f"Anomaly Detected on {equipment_id}: {anomaly_details[0]}"
        else:
            diagnosis = f"Normal Operation — {equipment_id} sensors nominal."

    trace = {
        "agent": "Diagnostic",
        "action": "Isolation Forest + XGBoost/SHAP (AI4I 2020) → LLM severity classification",
        "result": (
            f"[{alert_level}] {diagnosis[:100]} | "
            f"XGB: {ml_prob:.0%} {failure_type} | AUC={model_auc:.3f}"
        ),
        "health_score": health_score,
        "anomaly_score": ad_result["overall_anomaly_score"],
        "alert_level": alert_level,
        "ml_failure_probability": ml_prob,
        "predicted_failure_type": failure_type,
        "llm_reasoning": llm_reasoning[:200],
        "sensors_analyzed": list(per_sensor_scores.keys()),
    }
    traces = _append_trace(state, trace)

    return {
        "diagnosis": diagnosis,
        "health_score": health_score,
        "anomaly_detected": anomaly_detected,
        "anomaly_scores": per_sensor_scores,
        "anomaly_details": anomaly_details,
        "alert_level": alert_level,
        # XGBoost + SHAP results
        "ml_failure_probability": ml_prob,
        "predicted_failure_type": failure_type,
        "failure_type_label": failure_label,
        "shap_values": shap_values,
        "shap_top_features": shap_top,
        "model_auc": model_auc,
        "agent_traces": traces,
    }


# ─────────────────────────────────────────
# 2. KNOWLEDGE RETRIEVAL AGENT
#    FAISS semantic search over Tata Steel SOPs — runs before RootCause
#    so LLM gets full SOP context for causal reasoning
# ─────────────────────────────────────────
def knowledge_retrieval_agent(state: MaintenanceState) -> Dict[str, Any]:
    diagnosis = state.get("diagnosis", "")
    equipment_id = state.get("equipment_id", "Unknown")
    user_message = state.get("messages", [])[-1].content if state.get("messages") else ""
    sensor_data = state.get("sensor_data", {})

    fault_type, _ = get_dominant_fault_type(sensor_data)
    query = f"{user_message} {diagnosis} {fault_type} {equipment_id} maintenance procedure failure"

    try:
        results = retrieve(query, k=4)
        if not results:
            results = retrieve_for_fault(fault_type, equipment_type="pump", k=3)
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        results = []

    context_parts = []
    sources = []
    for r in results:
        context_parts.append(f"[{r['id']}] {r['title']}:\n{r['content']}")
        sources.append(f"{r['id']}: {r['title']} (relevance: {r['score']:.2f})")

    retrieved_context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."

    trace = {
        "agent": "KnowledgeRetrieval",
        "action": f"FAISS semantic search — {len(results)} SOP/failure-report documents retrieved",
        "result": f"Retrieved: {', '.join(r['id'] for r in results)}" if results else "No documents retrieved",
        "sources": sources,
        "query": query[:150],
    }
    traces = _append_trace(state, trace)

    return {
        "retrieved_context": retrieved_context,
        "retrieved_sources": sources,
        "agent_traces": traces,
    }


# ─────────────────────────────────────────
# 3. ROOT CAUSE AGENT
#    LLM reasons over sensor evidence + FAISS SOP context to identify
#    the precise failure mechanism — causal chain, not just symptom labelling
# ─────────────────────────────────────────

class RootCauseOutput(BaseModel):
    root_cause: str = Field(
        description="One precise sentence naming the primary failure mechanism (e.g. 'Blocked lubrication filter causing oil starvation — metal-to-metal contact imminent')"
    )
    causal_chain: str = Field(
        description="Step-by-step causal chain: what triggered what, referencing specific sensor readings (max 3 steps)"
    )
    primary_mechanism: str = Field(
        description="One of: lubrication_failure, bearing_wear, mechanical_imbalance, impeller_wear, thermal_overload, electrical_fault, normal_operation"
    )
    confidence: str = Field(
        description="HIGH / MEDIUM / LOW — based on how many independent sensor signals corroborate the cause"
    )


def root_cause_agent(state: MaintenanceState) -> Dict[str, Any]:
    diagnosis       = state.get("diagnosis", "")
    sensor_data     = state.get("sensor_data", {})
    anomaly_details = state.get("anomaly_details", [])
    equipment_id    = state.get("equipment_id", "Unknown")
    retrieved_context = state.get("retrieved_context", "")
    alert_level     = state.get("alert_level", "NORMAL")
    shap_top        = state.get("shap_top_features", [])
    failure_label   = state.get("failure_type_label", "No Failure Detected")

    temp      = float(sensor_data.get("temperature", 65))
    vib       = float(sensor_data.get("vibration", 0.30))
    pressure  = float(sensor_data.get("pressure", 100))
    oil_temp  = float(sensor_data.get("oil_temp", 52))
    current   = float(sensor_data.get("motor_current", 14))

    # Build sensor evidence list (used as fallback and LLM context)
    evidence = []
    if temp > 85:
        evidence.append(f"Bearing temperature {temp:.1f}°C — +{temp-65:.1f}°C above 65°C nominal (85°C alarm threshold breached)")
    elif temp > 78:
        evidence.append(f"Bearing temperature {temp:.1f}°C — elevated, approaching 85°C alarm threshold")
    if oil_temp > 65:
        evidence.append(f"Oil temperature {oil_temp:.1f}°C — +{oil_temp-52:.1f}°C above 52°C nominal (lubrication degradation signal)")
    elif oil_temp > 58:
        evidence.append(f"Oil temperature {oil_temp:.1f}°C — marginally elevated above 52°C nominal")
    if vib > 0.50:
        evidence.append(f"Vibration {vib:.3f} mm/s — ISO 10816-3 Zone C (long-term operation unsatisfactory)")
    elif vib > 0.35:
        evidence.append(f"Vibration {vib:.3f} mm/s — ISO 10816-3 Zone B (acceptable short-term only)")
    if pressure < 85:
        evidence.append(f"Discharge pressure {pressure:.1f} PSI — {90-pressure:.1f} PSI below 90 PSI nominal (impeller/suction line suspect)")
    if current > 17:
        evidence.append(f"Motor current {current:.1f} A — elevated above 15 A nominal (mechanical overload or misalignment)")
    if anomaly_details:
        evidence.extend(anomaly_details[:3])

    shap_summary = ", ".join(f"{s['feature']}={s['shap']:+.3f}" for s in shap_top[:4]) if shap_top else "N/A"

    # Rule-based fallback (used when LLM fails or unavailable)
    if temp > 80 and oil_temp > 58:
        fallback_cause = f"Lubrication failure on {equipment_id} — oil temperature {oil_temp:.1f}°C combined with bearing temperature {temp:.1f}°C indicates blocked supply line or degraded oil; metal-to-metal contact risk"
        fallback_mechanism = "lubrication_failure"
    elif temp > 80 and vib > 0.50:
        fallback_cause = f"Bearing mechanical wear on {equipment_id} — simultaneous temperature rise {temp:.1f}°C and vibration {vib:.3f} mm/s indicates bearing race deterioration"
        fallback_mechanism = "bearing_wear"
    elif vib > 0.60:
        fallback_cause = f"Mechanical imbalance or coupling misalignment on {equipment_id} — vibration {vib:.3f} mm/s dominant without proportional temperature rise"
        fallback_mechanism = "mechanical_imbalance"
    elif pressure < 88:
        fallback_cause = f"Impeller wear or suction line restriction on {equipment_id} — discharge pressure {pressure:.1f} PSI below 90 PSI nominal with normal vibration profile"
        fallback_mechanism = "impeller_wear"
    elif current > 17:
        fallback_cause = f"Electrical overload or shaft misalignment on {equipment_id} — motor current {current:.1f} A elevated above 15 A nominal"
        fallback_mechanism = "electrical_fault"
    else:
        fallback_cause = f"No significant fault detected on {equipment_id} — all sensors within nominal operating envelope"
        fallback_mechanism = "normal_operation"

    root_cause_final = fallback_cause
    causal_chain_final = " → ".join(evidence[:3]) if evidence else "All sensors nominal — no causal chain identified"
    llm_enhanced = False
    rc_confidence = "LOW"

    # ── LLM: reason over sensor evidence + FAISS SOP context ──
    _skip_rc_llm = alert_level == "NORMAL" and not evidence
    llm = None if _skip_rc_llm else _get_fast_llm(temperature=0.1, max_tokens=200)
    if llm:
        try:
            structured_llm = llm.with_structured_output(RootCauseOutput)
            sop_excerpt = retrieved_context[:700] if retrieved_context else "No SOP context."

            prompt = f"""Tata Steel RCA specialist. Equipment: {equipment_id} ({alert_level})
Diagnosis: {diagnosis} | XGBoost: {failure_label} | SHAP: {shap_summary}
Sensors: T={temp:.1f}°C(nom65) Vib={vib:.3f}mm/s(nom0.3) Oil={oil_temp:.1f}°C(nom52) P={pressure:.1f}PSI Current={current:.1f}A
Evidence: {"; ".join(evidence[:3]) if evidence else "none"}
SOP context: {sop_excerpt}

Identify PRIMARY root cause mechanism. primary_mechanism must be one of: lubrication_failure, bearing_wear, mechanical_imbalance, impeller_wear, thermal_overload, electrical_fault, normal_operation
confidence: HIGH=3+ signals, MEDIUM=2 signals, LOW=1 signal"""

            rc_result = structured_llm.invoke(prompt)
            root_cause_final   = rc_result.root_cause
            causal_chain_final = rc_result.causal_chain
            fallback_mechanism = rc_result.primary_mechanism
            rc_confidence      = rc_result.confidence
            llm_enhanced       = True
            logger.info(f"RootCause LLM: {fallback_mechanism} ({rc_confidence}) — {root_cause_final[:80]}")
        except Exception as e:
            logger.warning(f"RootCause LLM failed: {e} — using rule-based fallback")

    trace = {
        "agent": "RootCause",
        "action": "LLM causal chain analysis over sensor evidence + FAISS SOP context" if llm_enhanced else "Rule-based causal analysis (LLM unavailable)",
        "result": root_cause_final[:200],
        "evidence_count": len(evidence),
        "primary_mechanism": fallback_mechanism,
        "rc_confidence": rc_confidence,
        "llm_enhanced": llm_enhanced,
    }
    traces = _append_trace(state, trace)

    return {
        "root_cause": root_cause_final,
        "causal_chain": causal_chain_final,
        "primary_mechanism": fallback_mechanism,
        "root_cause_evidence": evidence,
        "evidence_chain": evidence,
        "agent_traces": traces,
    }


# ─────────────────────────────────────────
# 4. PREDICTIVE MAINTENANCE AGENT
#    Tool: Weibull degradation model (physics) → gives RUL numbers
#    Decision-maker: LLM assesses risk and generates work orders from SOP context
#    No hardcoded risk matrix math, no if/elif action lists
# ─────────────────────────────────────────
def predictive_maintenance_agent(state: MaintenanceState) -> Dict[str, Any]:
    sensor_data = state.get("sensor_data", {})
    diagnosis = state.get("diagnosis", "")
    equipment_id = state.get("equipment_id", "Unknown")
    alert_level = state.get("alert_level", "NORMAL")
    root_cause = state.get("root_cause", "")
    retrieved_context = state.get("retrieved_context", "")

    eq_id_lower = equipment_id.lower()
    equipment_type = (
        "furnace"  if "blast" in eq_id_lower or "furnace" in eq_id_lower
        else "mill"    if "mill" in eq_id_lower or "rolling" in eq_id_lower
        else "conveyor" if "conveyor" in eq_id_lower
        else "fan"     if "fan" in eq_id_lower or "cooling" in eq_id_lower
        else "pump"
    )

    # ── Tool: Weibull physics model ──
    health_index = compute_health_index(sensor_data)
    fault_type, _ = get_dominant_fault_type(sensor_data)
    if "Normal Operation" in diagnosis:
        fault_type = "normal_operation"
    rul_result = estimate_rul(sensor_data, health_index, equipment_type, fault_type)

    failure_prob = rul_result["failure_probability"]
    rul = rul_result["predicted_rul_days"]
    maintenance_priority = rul_result["maintenance_priority"]

    # Financial context for LLM (all values in INR)
    from agents.rul_predictor import EQUIPMENT_PARAMS as _EQ_PARAMS
    _p = _EQ_PARAMS.get(equipment_type, _EQ_PARAMS["default"])
    loss_per_hr   = _p["production_loss_per_hr"]
    planned_cost  = _p["planned_maintenance_cost"]
    emergency_cost = _p["emergency_repair_cost"]

    expected_downtime_hrs = max(4.0, (1.0 - health_index / 100.0) * 24.0)
    financial_exposure_inr = round(failure_prob * (expected_downtime_hrs * loss_per_hr + emergency_cost), 0)

    # Base risk level from Weibull output (LLM may refine this)
    risk_level    = "Critical" if failure_prob > 0.6 else "High" if failure_prob > 0.4 else "Medium" if failure_prob > 0.2 else "Low"
    risk_reasoning = f"Weibull model: {failure_prob*100:.0f}% failure probability, {rul:.1f} days RUL, Health {health_index:.0f}% — {fault_type.replace('_',' ').title()} detected."
    root_cause    = state.get("root_cause", "")
    primary_mech  = state.get("primary_mechanism", "unknown")
    retrieved_context = state.get("retrieved_context", "")
    shap_top      = state.get("shap_top_features", [])
    _t = sensor_data.get("temperature", 70)
    _v = sensor_data.get("vibration", 0.3)
    _o = sensor_data.get("oil_temp", 55)
    _c = sensor_data.get("motor_current", 14)
    _p_val = sensor_data.get("pressure", 95)
    shap_summary  = ", ".join(f"{s['feature']}={s['shap']:+.3f}" for s in shap_top[:4]) if shap_top else "N/A"

    # Rule-based fallback work orders (used when LLM fails)
    fallback_actions = []
    if alert_level in ("EMERGENCY", "CRITICAL"):
        fallback_actions.append({"action": f"Initiate controlled shutdown of {equipment_id} — failure risk imminent; isolate per LOTO (SOP-SHUTDOWN-001 §3.1)", "priority": "P1", "sop_reference": "SOP-SHUTDOWN-001 §3.1", "estimated_time": "30 min", "type": "corrective"})
    if _t >= 85 or _o >= 65:
        fallback_actions.append({"action": "Flush lubrication system and replace inline oil filter — check supply line for blockage", "priority": "P1", "sop_reference": "SOP-LUBRICATION-001 §2.1", "estimated_time": "2 hours", "type": "corrective"})
    if _v >= 0.50:
        fallback_actions.append({"action": "FFT vibration spectrum analysis — isolate BPFI/BPFO bearing fault frequency and confirm bearing condition", "priority": "P1", "sop_reference": "SOP-VIBRATION-001 §2.2", "estimated_time": "1 hour", "type": "diagnostic"})
    if _t >= 78 or _v >= 0.50:
        fallback_actions.append({"action": f"Replace bearing kit (SKF 6205) on {equipment_id} — stock available at Central Store", "priority": maintenance_priority, "sop_reference": "SOP-BEARING-001 §4.3", "estimated_time": "4 hours", "type": "replacement"})
    if _c >= 17:
        fallback_actions.append({"action": "Check shaft alignment with dial indicator — correct if total indicator reading > 0.05 mm", "priority": "P2", "sop_reference": "SOP-ALIGNMENT-001 §2", "estimated_time": "2 hours", "type": "corrective"})
    if _p_val < 88:
        fallback_actions.append({"action": "Inspect impeller and suction strainer for wear or blockage — measure clearance against OEM spec", "priority": "P2", "sop_reference": "SOP-PUMP-001 §3.2", "estimated_time": "3 hours", "type": "diagnostic"})
    if not fallback_actions:
        fallback_actions.append({"action": f"Continue routine monitoring per PM schedule for {equipment_id} — log every 8-hour shift", "priority": "Routine", "sop_reference": "PM-GUIDE-001 §4", "estimated_time": "1 hour", "type": "routine"})

    recommended_actions = fallback_actions
    llm_generated_actions = False

    # ── LLM: generate SOP-grounded work orders from Weibull + RCA context ──
    _skip_pm_llm = maintenance_priority == "Routine" and failure_prob < 0.20
    llm = None if _skip_pm_llm else _get_fast_llm(temperature=0.15, max_tokens=350)
    if llm:
        try:
            structured_llm = llm.with_structured_output(MaintenancePlan)
            sop_excerpt    = retrieved_context[:700] if retrieved_context else "No SOP context."

            prompt = f"""Tata Steel PM Engineer. Generate 3-5 work orders for {equipment_id} ({equipment_type}, {alert_level}).
Root cause: {root_cause} | Mechanism: {primary_mech}
Weibull: Prob={failure_prob*100:.0f}% RUL={rul:.1f}d Health={health_index:.0f}% Priority={maintenance_priority}
Sensors: T={_t}°C Vib={_v:.3f} Oil={_o}°C Current={_c}A P={_p_val}PSI | SHAP={shap_summary}
Financial: Loss=₹{loss_per_hr:,}/hr Planned=₹{planned_cost:,} Emergency=₹{emergency_cost:,}
SOP context: {sop_excerpt}

Rules: P1=now P2=24h P3=week Routine=PM. Name specific parts. Cover diagnostic+corrective+preventive.
risk_level: Critical|High|Medium|Low"""

            pm_result = structured_llm.invoke(prompt)
            risk_level  = pm_result.risk_level
            risk_reasoning = pm_result.risk_reasoning
            llm_actions = [
                {
                    "action":         a.action,
                    "priority":       a.priority,
                    "sop_reference":  a.sop_reference,
                    "estimated_time": a.estimated_time,
                    "type":           a.type,
                }
                for a in (pm_result.recommended_actions or [])
            ]
            if llm_actions:
                recommended_actions   = llm_actions
                llm_generated_actions = True
                logger.info(f"PredictiveMaintenance LLM: {len(llm_actions)} work orders | Risk={risk_level}")
        except Exception as e:
            logger.warning(f"PredictiveMaintenance LLM failed: {e} — using rule-based fallback")

    # Build risk_assessment dict (used by BusinessImpact + ExecutiveIntelligence)
    eq_criticality = 5 if "pump" in eq_id_lower else 4 if "furnace" in eq_id_lower else 3
    safety_risk = (
        "Critical — immediate personnel hazard; enforce 5m exclusion zone" if alert_level == "EMERGENCY" else
        "Significant — secondary equipment damage risk; assign dedicated watchperson" if alert_level == "CRITICAL" else
        "Moderate — controlled risk; standard PPE required" if alert_level == "WARNING" else
        "Low — no immediate safety concern"
    )
    risk_assessment = {
        "level": risk_level,
        "risk_reasoning": risk_reasoning,
        "financial_exposure_inr": financial_exposure_inr,
        "expected_downtime_hours": round(expected_downtime_hrs, 1),
        "safety_risk": safety_risk,
        "production_loss_per_hour_inr": loss_per_hr,
        "planned_vs_emergency_ratio": f"1:{round(emergency_cost/planned_cost, 1)}",
        "equipment_criticality": eq_criticality,
    }

    trace = {
        "agent": "PredictiveMaintenance",
        "action": "Weibull RUL + LLM SOP-grounded work order generation" if llm_generated_actions else "Weibull RUL + rule-based work orders (LLM unavailable)",
        "result": (
            f"RUL: {rul_result['predicted_rul_days']}d [{rul_result['rul_lower_bound']}–{rul_result['rul_upper_bound']}d] | "
            f"Risk: {risk_level} | {len(recommended_actions)} work orders | Priority: {maintenance_priority}"
        ),
        "health_index": health_index,
        "fault_type": fault_type,
        "rul_days": rul,
        "failure_probability": failure_prob,
        "priority": maintenance_priority,
        "llm_generated_actions": llm_generated_actions,
    }
    traces = _append_trace(state, trace)

    return {
        "predicted_rul_days": rul_result["predicted_rul_days"],
        "rul_lower_bound": rul_result["rul_lower_bound"],
        "rul_upper_bound": rul_result["rul_upper_bound"],
        "failure_probability": failure_prob,
        "health_score": health_index,
        "maintenance_priority": maintenance_priority,
        "risk_assessment": risk_assessment,
        "recommended_actions": recommended_actions,
        "work_order_generated": True,
        "agent_traces": traces,
    }


# ─────────────────────────────────────────
# 5. BUSINESS IMPACT AGENT
#    ₹ ROI calculation + spares urgency + approval gate
#    Financial math is correct as code — not rule-based AI logic
# ─────────────────────────────────────────
def business_impact_agent(state: MaintenanceState) -> Dict[str, Any]:
    failure_prob = state.get("failure_probability", 0.0)
    rul = state.get("predicted_rul_days", 30.0)
    health_score = state.get("health_score", 75.0)
    equipment_id = state.get("equipment_id", "Unknown")
    risk_assessment = state.get("risk_assessment", {})
    maintenance_priority = state.get("maintenance_priority", "P2")

    eq_lower = equipment_id.lower()
    _biz_eq_type = (
        "furnace"  if "blast" in eq_lower or "furnace" in eq_lower
        else "mill"    if "mill" in eq_lower or "rolling" in eq_lower
        else "conveyor" if "conveyor" in eq_lower
        else "fan"     if "fan" in eq_lower or "cooling" in eq_lower
        else "pump"
    )
    from agents.rul_predictor import EQUIPMENT_PARAMS as _BIZ_PARAMS
    _bp = _BIZ_PARAMS.get(_biz_eq_type, _BIZ_PARAMS["default"])
    loss_per_hour_inr   = _bp["production_loss_per_hr"]
    planned_cost_inr    = _bp["planned_maintenance_cost"]
    emergency_cost_inr  = _bp["emergency_repair_cost"]

    expected_downtime_hrs = max(4.0, (1.0 - health_score / 100.0) * 48.0)
    production_loss_inr = failure_prob * expected_downtime_hrs * loss_per_hour_inr
    roi = round(production_loss_inr / max(planned_cost_inr, 1), 1)

    if rul < 1:
        action_window = "IMMEDIATE — within 2 hours"
        urgency = "CRITICAL"
    elif rul < 3:
        action_window = "Within 24 hours"
        urgency = "HIGH"
    elif rul < 7:
        action_window = "Within 3 days"
        urgency = "MEDIUM"
    else:
        action_window = "Within next PM cycle"
        urgency = "LOW"

    if failure_prob > 0.6:
        spares_action = "Initiate emergency procurement — bearing SKF 6315, seal kit"
        spares_lead_time = "2-4 hours (local vendor)"
    elif failure_prob > 0.3:
        spares_action = "Reserve spares from central store — check availability"
        spares_lead_time = "Same day"
    else:
        spares_action = "Standard procurement via SAP MM module"
        spares_lead_time = "3-5 days"

    auto_approve = risk_assessment.get("level") in ("Low",) and maintenance_priority == "Routine"

    business_impact = {
        "production_loss_inr": round(production_loss_inr),
        "planned_maintenance_cost_inr": planned_cost_inr,
        "emergency_maintenance_cost_inr": emergency_cost_inr,
        "roi_of_preventive_action": roi,
        "action_window": action_window,
        "urgency": urgency,
        "spares_procurement": spares_action,
        "spares_lead_time": spares_lead_time,
        "expected_downtime_hours": round(expected_downtime_hrs, 1),
        "loss_per_hour_inr": loss_per_hour_inr,
        "safety_risk": risk_assessment.get("safety_risk", "Moderate — controlled risk"),
        "industry_benchmark": "₹28L/day avg unplanned downtime — Tata Steel internal benchmark",
        "environmental_impact": "Moderate energy waste due to degraded pump efficiency" if health_score < 60 else "Minimal environmental impact",
        "approval_required": not auto_approve,
        "auto_approved": auto_approve,
    }

    trace = {
        "agent": "BusinessImpact",
        "action": "₹ ROI + spares urgency + engineer approval gate",
        "result": (
            f"ROI {roi}:1 | Loss if ignored: ₹{production_loss_inr/100000:.1f}L | "
            f"Action: {action_window} | {'Auto-approved' if auto_approve else 'Engineer approval required'}"
        ),
        "roi": roi,
        "urgency": urgency,
    }
    traces = _append_trace(state, trace)

    return {
        "business_impact": business_impact,
        "agent_traces": traces,
    }


# ─────────────────────────────────────────
# 6. EXECUTIVE INTELLIGENCE AGENT
#    LLM composes the final XAI report for plant leadership
#    with confidence scoring, evidence chain, and ₹ business context
# ─────────────────────────────────────────
def executive_intelligence_agent(state: MaintenanceState) -> Dict[str, Any]:
    equipment_id = state.get("equipment_id", "Unknown")
    diagnosis = state.get("diagnosis", "")
    root_cause = state.get("root_cause", "")
    rul = state.get("predicted_rul_days", 30.0)
    rul_lower = state.get("rul_lower_bound", rul * 0.7)
    rul_upper = state.get("rul_upper_bound", rul * 1.5)
    failure_prob = state.get("failure_probability", 0.5)
    health_score = state.get("health_score", 75.0)
    risk_assessment = state.get("risk_assessment", {})
    evidence_chain = state.get("evidence_chain", [])
    retrieved_sources = state.get("retrieved_sources", [])
    maintenance_priority = state.get("maintenance_priority", "P2")
    actions = state.get("recommended_actions", [])
    alert_level = state.get("alert_level", "NORMAL")
    business_impact = state.get("business_impact", {})

    # Multi-factor confidence scoring
    anomaly_score = abs(state.get("anomaly_scores", {}).get("temperature", 0))
    evidence_count = len(evidence_chain)
    rag_confidence = 0.88 if retrieved_sources else 0.60
    confidence_factors = [
        min(0.95, 0.50 + anomaly_score * 0.10),
        min(0.95, 0.50 + evidence_count * 0.08),
        rag_confidence,
    ]
    fb_adj = state.get("feedback_adjustments", {}).get("global", 1.0)
    confidence_score = round(min(0.97, sum(confidence_factors) / len(confidence_factors) * fb_adj), 2)

    llm = _get_llm(temperature=0.3)
    xai_explanation = ""

    # Extract user's question early so fallback can also use it
    messages = state.get("messages", [])
    user_question = ""
    for m in reversed(messages):
        if hasattr(m, "type") and m.type == "human":
            user_question = m.content
            break
        if hasattr(m, "content") and not hasattr(m, "type"):
            user_question = m.content
            break

    if llm:
        try:
            top_actions = [a["action"] for a in actions[:3]]
            roi = business_impact.get("roi_of_preventive_action", "N/A")
            loss_inr = business_impact.get("production_loss_inr", 0)
            causal_chain = state.get("causal_chain", "")
            primary_mech = state.get("primary_mechanism", "unknown")

            # Derive equipment type + spare parts for this equipment
            eq_id_lower = equipment_id.lower()
            eq_type = (
                "furnace" if "blast" in eq_id_lower or "furnace" in eq_id_lower
                else "mill" if "mill" in eq_id_lower or "rolling" in eq_id_lower
                else "conveyor" if "conveyor" in eq_id_lower
                else "fan" if "fan" in eq_id_lower or "cooling" in eq_id_lower
                else "pump"
            )
            SPARE_CTX = {
                "pump":     "✓ Bearing Kit SKF 6205 — In Stock (Warehouse, Central Store)\n  ⚠ Mechanical Seal Type-II — Limited (3–5 days, SAIL Stores)\n  ✗ Impeller 316 SS — Out of Stock (14–21 days, OEM Kirloskar)\n  ✓ Coupling Insert (Poly) — In Stock (Warehouse)\n  ✓ Lubrication Oil VG68 — In Stock (Warehouse)",
                "conveyor": "✓ Conveyor Belt Section 5m — In Stock (Central Store)\n  ✓ Idler Roller Set — In Stock (Mechanical Store)\n  ✗ Drive Chain 80H — Out of Stock (10–14 days, OEM Rexnord)\n  ⚠ Sprocket Z=21 — Limited (5–7 days, SAIL Stores)",
                "fan":      "⚠ Fan Blade Assembly — Limited (7–10 days, OEM Howden)\n  ✓ Motor Bearing FAG 6308 — In Stock (Central Store)\n  ✓ V-Belt Set B-Section — In Stock (Central Store)\n  ✗ Fan Shaft Seal — Out of Stock (21–28 days, OEM Howden)",
                "furnace":  "✓ Tuyere Assembly — In Stock (Central Store)\n  ✗ Cooling Stave Cu — Out of Stock (21–28 days, SMS Group)\n  ✓ Thermocouple Type-K — In Stock (Instrumentation Store)\n  ✗ Refractory Brick Grade C — Out of Stock (35–42 days, Vesuvius India)",
                "mill":     "✗ Work Roll Forged Steel — Out of Stock (14–21 days, Bhilai Roll Plant)\n  ✓ Bearing Housing Roll — In Stock (Rolling Mill Store)\n  ✓ Hydraulic Cylinder Seal Kit — In Stock (Central Store)\n  ⚠ Spindle Coupling Insert — Limited (5–7 days, SAIL Stores)",
            }
            spare_parts_table = SPARE_CTX.get(eq_type, SPARE_CTX["pump"])

            sensor_data = state.get("sensor_data", {})
            t  = sensor_data.get("temperature", 70)
            v  = sensor_data.get("vibration", 0.3)
            o  = sensor_data.get("oil_temp", 55)
            c  = sensor_data.get("motor_current", 14)
            p  = sensor_data.get("pressure", 95)

            mon_freq = ("every 30 min" if alert_level == "EMERGENCY"
                        else "every 2 hours" if alert_level == "CRITICAL"
                        else "every 4 hours" if alert_level == "WARNING"
                        else "every 8 hours")

            # Expanded question-type detection — each branch gets a focused prompt
            q = user_question.lower()
            if any(k in q for k in ["spare", "part", "stock", "order", "procure", "lead time", "inventory", "bearing kit", "seal", "component", "impeller", "coupling"]):
                q_type = "SPARE_PARTS"
            elif any(k in q for k in ["ppe", "protective equipment", "what to wear", "what gear", "gloves", "helmet", "hard hat"]) or ("wear" in q and any(k in q for k in ["maintenance", "team", "technician", "engineer"])):
                q_type = "PPE"
            elif any(k in q for k in ["safe", "danger", "hazard", "harm", "keep running", "fire", "explosion", "risk if"]):
                q_type = "SAFETY"
            elif any(k in q for k in ["cost", "rupee", "inr", "money", "roi", "financial", "loss", "budget", "expensive", "breakdown cost", "repair cost"]):
                q_type = "FINANCIAL"
            elif any(k in q for k in ["shutdown", "shut down", "turn off", "restart", "power on", "stop the", "isolate", "de-energize", "loto", "lock out"]):
                q_type = "SHUTDOWN"
            elif any(k in q for k in ["how often", "frequency", "how frequent", "interval", "check every", "monitoring schedule", "vibration level triggers"]):
                q_type = "MONITORING"
            elif any(k in q for k in ["rul", "remaining", "how many days", "when will", "expire", "life left", "how long", "before complete", "before failure", "days of useful"]):
                q_type = "RUL"
            elif any(k in q for k in ["caused", "why is", "why does", "root cause", "what caused", "reason for", "failure mode", "what is causing", "what triggered"]):
                q_type = "ROOT_CAUSE"
            elif any(k in q for k in ["procedure", "step-by-step", "sop", "which sop", "repair procedure", "fastest repair", "how do i", "how to"]):
                q_type = "PROCEDURE"
            elif any(k in q for k in ["diagnose", "diagnosis", "current condition", "condition", "what is happening", "analyse", "analyze", "what's wrong", "explain the"]):
                q_type = "DIAGNOSIS"
            elif any(k in q for k in ["action", "fix", "repair", "recommend", "what should", "what to do", "next step", "reduce load", "what maintenance", "urgent attention"]):
                q_type = "ACTIONS"
            elif any(k in q for k in ["compare", "benchmark", "similar equipment", "how does this compare", "typical mtbf", "extend the maintenance", "extend maintenance"]):
                q_type = "COMPARISON"
            else:
                q_type = "GENERAL"

            # Build focused context — each type gets only what it needs (~300 tokens)
            base_ctx = (
                f"Equipment: {equipment_id} ({eq_type}) | Alert: {alert_level} | Health: {health_score:.0f}% | "
                f"Prob: {failure_prob*100:.0f}% | RUL: {rul:.1f}d [{rul_lower:.1f}–{rul_upper:.1f}d] | Priority: {maintenance_priority}\n"
                f"Diagnosis: {diagnosis}\nRoot Cause: {root_cause}\n"
                f"Sensors: T={t}°C Vib={v:.3f} Oil={o}°C Current={c}A P={p}PSI"
            )

            if q_type == "SPARE_PARTS":
                focused = f"{base_ctx}\nSpare parts:\n{spare_parts_table}\nTask: List parts status and procurement urgency given RUL={rul:.1f}d."
            elif q_type == "PPE":
                focused = (f"{base_ctx}\nTask: List the specific PPE required for maintenance on this {eq_type} under {alert_level} conditions. "
                           f"Cover: minimum standard PPE + any extra items given detected faults ({primary_mech}). Be specific and practical.")
            elif q_type == "SAFETY":
                focused = f"{base_ctx}\nTask: Assess safety risk. If CRITICAL/EMERGENCY list specific hazards with sensor values. If NORMAL confirm safe with standard PPE."
            elif q_type == "FINANCIAL":
                focused = (f"{base_ctx}\nCosts: Planned=₹{business_impact.get('planned_maintenance_cost_inr',150000):,} "
                           f"Emergency=₹{business_impact.get('emergency_maintenance_cost_inr',500000):,} "
                           f"Loss/hr=₹{business_impact.get('loss_per_hour_inr',50000):,} ROI={roi}:1 "
                           f"Action window={business_impact.get('action_window','N/A')}\nTask: Give financial impact analysis with ₹ numbers.")
            elif q_type == "SHUTDOWN":
                focused = f"{base_ctx}\nTask: Answer the shutdown/restart question directly with step-by-step SOP guidance. State clearly if immediate shutdown is required given current {alert_level} status."
            elif q_type == "MONITORING":
                focused = f"{base_ctx}\nMonitor {mon_freq}. Thresholds: T>90°C emergency, Vib>0.70mm/s emergency.\nTask: Give monitoring schedule with specific sensor thresholds and current readings."
            elif q_type == "RUL":
                focused = f"{base_ctx}\nTask: Explain remaining useful life estimate with 80% CI [{rul_lower:.1f}–{rul_upper:.1f}d], what the failure probability means, and the maintenance deadline."
            elif q_type == "ROOT_CAUSE":
                focused = (f"{base_ctx}\nCausal chain: {causal_chain}\nPrimary mechanism: {primary_mech}\n"
                           f"Task: Explain clearly what caused the current condition — trace the causal chain using specific sensor readings. Do not list actions.")
            elif q_type == "PROCEDURE":
                focused = (f"{base_ctx}\nActions: {'; '.join(top_actions[:3])}\n"
                           f"SOPs: {', '.join(r.split(':')[0] for r in retrieved_sources[:2]) if retrieved_sources else 'SOP-PUMP-001'}\n"
                           f"Task: Give numbered step-by-step procedure directly answering '{user_question}'. Reference specific SOP sections.")
            elif q_type == "DIAGNOSIS":
                focused = (f"{base_ctx}\nCausal chain: {causal_chain}\n"
                           f"Task: Give a clear, complete technical diagnosis. State: what is happening, which sensors confirm it, severity level, and single most urgent action. Do not discuss cost.")
            elif q_type == "ACTIONS":
                focused = (f"{base_ctx}\nPrioritised actions:\n" + "\n".join(f"  {i+1}. [{a.get('priority','P2')}] {a['action']} ({a.get('sop_reference','')})" for i, a in enumerate(actions[:4])) +
                           f"\nTask: Answer '{user_question}' — list specific actions in priority order. Be actionable. Include SOP references.")
            elif q_type == "COMPARISON":
                focused = (f"{base_ctx}\nTask: Answer the comparison/benchmarking question '{user_question}'. "
                           f"Use industry standards (ISO 10816-3 for vibration, typical MTBF values) and Tata Steel internal benchmarks where relevant.")
            else:
                focused = (f"{base_ctx}\nActions: {'; '.join(top_actions[:3])}\n"
                           f"Task: Answer ONLY this specific question: '{user_question}'. Give a direct, targeted answer — do NOT repeat the full diagnosis. 2–5 sentences.")

            prompt = f"""You are Stelos AI — Senior Reliability Engineer at Tata Steel Jamshedpur.

QUESTION: "{user_question}"

{focused}

STRICT RULES:
- Answer ONLY the question above. One topic. Do not mix in unrelated info.
- If asked about cost → give only ₹ numbers and ROI. Nothing else.
- If asked about RUL → give only days, probability, deadline. Nothing else.
- If asked about PPE → give only safety gear list. Nothing else.
- If asked about shutdown → give only steps. Nothing else.
- Use ₹ INR. Bold key numbers with **value**. Max 6 sentences or 5 bullets."""

            response = llm.invoke(prompt)
            xai_explanation = response.content.strip()
        except Exception as e:
            logger.warning(f"XAI summary failed: {e}")

    if not xai_explanation:
        from main import _smart_fallback_response, FLEET
        sensor_data = state.get("sensor_data", {})
        eq_info = FLEET.get(equipment_id, {})
        eq_type = eq_info.get("type", "pump")
        xai_explanation = _smart_fallback_response(
            equipment_id, user_question, sensor_data,
            health_score, rul,
            state.get("rul_lower_bound", round(rul * 0.7, 1)),
            state.get("rul_upper_bound", round(rul * 1.4, 1)),
            failure_prob, alert_level, maintenance_priority,
            state.get("failure_type_label", "Unknown Fault")
        )

    final_message = xai_explanation

    trace = {
        "agent": "ExecutiveIntelligence",
        "action": "LLM XAI report — synthesises all 6 agent outputs for plant leadership",
        "result": f"Confidence: {confidence_score:.0%} | {evidence_count} evidence items | {len(retrieved_sources)} SOP sources",
        "confidence_score": confidence_score,
    }
    traces = _append_trace(state, trace)

    return {
        "confidence_score": confidence_score,
        "xai_explanation": xai_explanation,
        "evidence_chain": evidence_chain,
        "messages": [AIMessage(content=final_message)],
        "agent_traces": traces,
    }
