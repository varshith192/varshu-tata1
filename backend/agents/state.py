from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class MaintenanceState(TypedDict):
    """
    Complete state for the Stelos AI maintenance decision workflow.
    """
    messages: Annotated[List[BaseMessage], add_messages]

    # Core inputs
    equipment_id: str
    sensor_data: Dict[str, Any]

    # Anomaly detection outputs
    anomaly_scores: Dict[str, float]        # per-sensor anomaly score (-1=anomaly, 1=normal)
    anomaly_detected: bool
    anomaly_details: List[str]              # human-readable anomaly descriptions

    # Diagnosis
    diagnosis: str
    health_score: float                     # 0-100 overall health index

    # Root cause
    root_cause: str
    root_cause_evidence: List[str]          # supporting evidence list
    causal_chain: Optional[str]             # step-by-step causal chain from RootCause agent
    primary_mechanism: Optional[str]        # lubrication_failure | bearing_wear | etc.

    # Knowledge retrieval
    retrieved_context: str                  # RAG retrieved text
    retrieved_sources: List[str]            # source document names

    # Predictive maintenance / RUL
    predicted_rul_days: float
    rul_lower_bound: float                  # 80% confidence lower bound
    rul_upper_bound: float                  # 80% confidence upper bound
    failure_probability: float

    # Risk assessment
    risk_assessment: Dict[str, Any]
    alert_level: str                        # NORMAL | WARNING | CRITICAL | EMERGENCY

    # Maintenance planning
    recommended_actions: List[Dict[str, Any]]
    maintenance_priority: str               # P1 | P2 | P3
    work_order_generated: bool

    # What-If simulation
    what_if_result: Optional[Dict[str, Any]]

    # Business impact
    business_impact: Optional[Dict[str, Any]]

    # XGBoost + SHAP (AI4I 2020 dataset)
    ml_failure_probability: Optional[float]
    predicted_failure_type: Optional[str]    # TWF | HDF | PWF | OSF | NONE
    failure_type_label: Optional[str]
    shap_values: Optional[Dict[str, float]]
    shap_top_features: Optional[List[Dict[str, Any]]]
    model_auc: Optional[float]

    # Explainability
    confidence_score: float                 # 0.0-1.0
    xai_explanation: str                    # full reasoning narrative
    evidence_chain: List[str]               # ordered chain of evidence

    # Feedback learning
    feedback_adjustments: Dict[str, float]  # agent → confidence multiplier

    # Routing
    next_agent: str
    agent_traces: List[Dict[str, Any]]
