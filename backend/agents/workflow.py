from langgraph.graph import StateGraph, END
from .state import MaintenanceState
from .nodes import (
    diagnostic_agent,
    knowledge_retrieval_agent,
    root_cause_agent,
    predictive_maintenance_agent,
    business_impact_agent,
    executive_intelligence_agent,
)


def build_workflow():
    workflow = StateGraph(MaintenanceState)

    # Register 6 agent nodes
    workflow.add_node("Diagnostic", diagnostic_agent)
    workflow.add_node("KnowledgeRetrieval", knowledge_retrieval_agent)
    workflow.add_node("RootCause", root_cause_agent)
    workflow.add_node("PredictiveMaintenance", predictive_maintenance_agent)
    workflow.add_node("BusinessImpact", business_impact_agent)
    workflow.add_node("ExecutiveIntelligence", executive_intelligence_agent)

    # Linear pipeline — KnowledgeRetrieval runs before RootCause
    # so the LLM gets full SOP context during causal reasoning
    workflow.add_edge("Diagnostic", "KnowledgeRetrieval")
    workflow.add_edge("KnowledgeRetrieval", "RootCause")
    workflow.add_edge("RootCause", "PredictiveMaintenance")
    workflow.add_edge("PredictiveMaintenance", "BusinessImpact")
    workflow.add_edge("BusinessImpact", "ExecutiveIntelligence")
    workflow.add_edge("ExecutiveIntelligence", END)

    workflow.set_entry_point("Diagnostic")

    return workflow.compile()


app_graph = build_workflow()
