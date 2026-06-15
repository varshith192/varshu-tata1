"""
NetworkX-based plant topology for Stelos AI.
Models the Jamshedpur plant as a directed dependency graph:
  node  = equipment unit
  edge  = A → B means B depends on A (A failure cascades to B)

Used by /api/plant/topology and /api/plant/impact/{equipment_id}.
"""
import networkx as nx
from typing import Dict, List, Any

# ── Node definitions (mirrors FLEET in main.py) ──────────────────────────────
_NODES: Dict[str, Dict] = {
    "Conveyor-B":    {"type": "conveyor", "location": "Raw Material Yard",    "criticality": "High",     "description": "Ore/coal feed to blast furnace and sinter plant"},
    "Pump-A":        {"type": "pump",     "location": "Blast Furnace #2",     "criticality": "High",     "description": "Cooling water pump — BF-2 shell circuit"},
    "Pump-B":        {"type": "pump",     "location": "Blast Furnace #3",     "criticality": "Critical", "description": "Cooling water pump — BF-3 shell circuit"},
    "Pump-C":        {"type": "pump",     "location": "Blast Furnace #4",     "criticality": "Critical", "description": "Cooling water pump — BF-4 shell circuit"},
    "Compressor-2":  {"type": "pump",     "location": "Oxygen Plant",         "criticality": "High",     "description": "Oxygen enrichment compressor for blast air"},
    "Power-Unit":    {"type": "pump",     "location": "Power Distribution",   "criticality": "High",     "description": "Auxiliary power supply — drives plant auxiliaries"},
    "Cooling-Fan-4": {"type": "fan",      "location": "Sinter Plant",         "criticality": "Medium",   "description": "Sinter cooling fan — cools hot sinter before conveying"},
    "Blast-Furnace": {"type": "furnace",  "location": "Blast Furnace #1",     "criticality": "Critical", "description": "Primary iron-making unit — hot metal production"},
    "Cooling-Unit":  {"type": "fan",      "location": "Steel Melting Shop",   "criticality": "Medium",   "description": "SMS cooling unit — temperature control for converters"},
    "Rolling-Mill":  {"type": "mill",     "location": "Hot Rolling Section",  "criticality": "Critical", "description": "Hot strip mill — converts slabs to finished steel"},
}

# ── Directed edges: (upstream, downstream, relationship label) ────────────────
_EDGES: List[tuple] = [
    # Raw material supply
    ("Conveyor-B",    "Blast-Furnace",  "raw_material_feed"),
    ("Conveyor-B",    "Cooling-Fan-4",  "sinter_feed"),
    # Cooling water for blast furnaces
    ("Pump-A",        "Blast-Furnace",  "cooling_water"),
    ("Pump-B",        "Blast-Furnace",  "cooling_water"),
    ("Pump-C",        "Blast-Furnace",  "cooling_water"),
    # Oxygen and power
    ("Compressor-2",  "Blast-Furnace",  "oxygen_enrichment"),
    ("Power-Unit",    "Blast-Furnace",  "auxiliary_power"),
    ("Power-Unit",    "Rolling-Mill",   "auxiliary_power"),
    # Sinter to rolling
    ("Cooling-Fan-4", "Rolling-Mill",   "sinter_supply"),
    # Hot metal flow
    ("Blast-Furnace", "Rolling-Mill",   "hot_metal"),
    # SMS cooling
    ("Cooling-Unit",  "Rolling-Mill",   "process_cooling"),
    ("Cooling-Unit",  "Cooling-Fan-4",  "auxiliary_cooling"),
]

# Downstream production impact of each node (tonnes/hour lost if it fails)
_PRODUCTION_IMPACT_TPH: Dict[str, float] = {
    "Blast-Furnace": 250.0,
    "Rolling-Mill":  180.0,
    "Conveyor-B":    200.0,
    "Pump-A":         80.0,
    "Pump-B":        150.0,
    "Pump-C":         90.0,
    "Compressor-2":  120.0,
    "Power-Unit":    180.0,
    "Cooling-Fan-4":  60.0,
    "Cooling-Unit":   40.0,
}

_INR_PER_TONNE = 45_000  # approximate hot rolled steel revenue


def _build_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    for node_id, attrs in _NODES.items():
        G.add_node(node_id, **attrs, production_impact_tph=_PRODUCTION_IMPACT_TPH.get(node_id, 0))
    for src, dst, rel in _EDGES:
        G.add_edge(src, dst, relationship=rel)
    return G


_GRAPH = _build_graph()


def get_topology_data() -> Dict[str, Any]:
    """Return full graph as JSON-serialisable dict for frontend rendering."""
    nodes = []
    for node_id, data in _GRAPH.nodes(data=True):
        nodes.append({
            "id":           node_id,
            "label":        node_id,
            **data,
        })

    edges = []
    for src, dst, data in _GRAPH.edges(data=True):
        edges.append({
            "source":       src,
            "target":       dst,
            "relationship": data.get("relationship", "depends_on"),
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes":         _GRAPH.number_of_nodes(),
            "total_edges":         _GRAPH.number_of_edges(),
            "critical_nodes":      [n for n, d in _GRAPH.nodes(data=True) if d.get("criticality") == "Critical"],
            "single_point_nodes":  _get_single_points(),
        }
    }


def get_cascade_impact(equipment_id: str, health_score: float = 0.0) -> Dict[str, Any]:
    """
    Return all downstream equipment affected if `equipment_id` fails,
    ranked by production impact.  health_score (0–100) scales severity.
    """
    if equipment_id not in _GRAPH:
        return {"affected": [], "total_production_loss_tph": 0, "total_loss_inr_per_hour": 0}

    # All nodes reachable downstream (BFS/DFS from the failing node)
    affected_ids = list(nx.descendants(_GRAPH, equipment_id))

    affected = []
    for aid in affected_ids:
        node_data = _GRAPH.nodes[aid]
        path = nx.shortest_path(_GRAPH, equipment_id, aid)
        affected.append({
            "equipment_id":        aid,
            "type":                node_data.get("type"),
            "location":            node_data.get("location"),
            "criticality":         node_data.get("criticality"),
            "production_impact_tph": node_data.get("production_impact_tph", 0),
            "dependency_path":     " → ".join(path),
            "hops":                len(path) - 1,
        })

    # Sort by direct vs indirect (hops) then by impact
    affected.sort(key=lambda x: (x["hops"], -x["production_impact_tph"]))

    own_impact = _PRODUCTION_IMPACT_TPH.get(equipment_id, 0)
    cascaded   = sum(a["production_impact_tph"] for a in affected)
    total_tph  = own_impact + cascaded

    severity = max(0.0, min(1.0, (100.0 - health_score) / 100.0)) if health_score > 0 else 1.0
    effective_tph = round(total_tph * severity, 1)
    loss_inr_per_hour = round(effective_tph * _INR_PER_TONNE / 1000, 0)  # ₹ per hour (tonne→₹)

    return {
        "equipment_id":           equipment_id,
        "own_impact_tph":         own_impact,
        "cascaded_equipment":     affected,
        "cascade_depth":          max((a["hops"] for a in affected), default=0),
        "total_production_loss_tph": effective_tph,
        "total_loss_inr_per_hour":   int(loss_inr_per_hour),
        "is_single_point_of_failure": equipment_id in _get_single_points(),
        "upstream_dependencies":  list(_GRAPH.predecessors(equipment_id)),
    }


def _get_single_points() -> List[str]:
    """Nodes whose removal disconnects the graph (articulation points in undirected view)."""
    undirected = _GRAPH.to_undirected()
    return list(nx.articulation_points(undirected))
