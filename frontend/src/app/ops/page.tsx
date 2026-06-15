"use client";

import { useState, useEffect, useRef, Dispatch, SetStateAction } from "react";
import {
  CheckCircle2, XCircle, Clock, RefreshCw,
  ChevronDown, ChevronUp, User, ClipboardList, ShieldCheck,
  Package, ThumbsUp, ThumbsDown, AlertTriangle, Zap,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useFleet } from "@/lib/fleetStore";

// ─── Types ───────────────────────────────────────────────────────────────────
type Action = { action: string; priority: string; sop_reference: string };

type LogEntry = {
  id: number;
  timestamp: string;
  equipment_id: string;
  location: string;
  alert_level: string;
  diagnosis: string;
  root_cause?: string;
  health_score: number;
  rul_days: number;
  failure_probability: number;
  maintenance_priority: string;
  recommended_actions: Action[];
  confidence_score?: number;
  work_order_id?: string;
  approved: boolean;
  approval_engineer?: string;
  approval_timestamp?: string;
  approval_notes?: string;
  auto_logged?: boolean;
};

type SparePart = {
  part_id: string;
  part_name: string;
  equipment_ids: string[];
  qty: number;
  unit: string;
  status: "In Stock" | "Low Stock" | "Out of Stock";
  supplier: string;
  lead_time_days: number;
  cost_inr: number;
};

type FeedbackStats = {
  total: number;
  confirmed: number;
  corrected: number;
  accuracy_pct: number;
  rag_augmented: number;
  by_equipment: { equipment_id: string; confirmed: number; corrected: number }[];
  latest_timestamp: string;
};

type HistoryItem = {
  woId: string;
  equipmentId: string;
  decision: "approved" | "rejected";
  engineer: string;
  timestamp: string;
  notes?: string;
};

// ─── Constants ───────────────────────────────────────────────────────────────
const ALERT_BADGE: Record<string, string> = {
  EMERGENCY: "bg-rose-100 text-rose-700 border-rose-200",
  CRITICAL:  "bg-rose-50  text-rose-600  border-rose-200",
  WARNING:   "bg-amber-50 text-amber-600 border-amber-200",
  NORMAL:    "bg-emerald-50 text-emerald-600 border-emerald-200",
};
const PRIORITY_BADGE: Record<string, string> = {
  P1: "bg-rose-100 text-rose-700", P2: "bg-amber-100 text-amber-700",
  P3: "bg-blue-100 text-blue-700", Routine: "bg-slate-100 text-slate-500",
};
const STATUS_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  "In Stock":     { bg: "#f0fdf4", text: "#166534", border: "#bbf7d0" },
  "Low Stock":    { bg: "#fffbeb", text: "#92400e", border: "#fde68a" },
  "Out of Stock": { bg: "#fef2f2", text: "#991b1b", border: "#fecaca" },
};

function hc(s: number) { return s >= 80 ? "#10b981" : s >= 60 ? "#f59e0b" : "#ef4444"; }
function rc(p: number) { return p > 0.6 ? "#ef4444" : p > 0.3 ? "#f59e0b" : "#10b981"; }
function fmtINR(n: number) { return n >= 100000 ? `₹${(n/100000).toFixed(1)}L` : `₹${n.toLocaleString()}`; }

// ─── Seed data ────────────────────────────────────────────────────────────────
const SEED: LogEntry[] = [
  { id: 3, timestamp: "2026-06-14T08:55:00", equipment_id: "Pump-B",        location: "Blast Furnace #3",  alert_level: "CRITICAL", diagnosis: "Bearing temperature 92.5°C — lubrication failure suspected",           root_cause: "Blocked lubrication filter — oil temperature 68.5°C; metal-to-metal contact imminent",        health_score: 44, rul_days: 4.3,  failure_probability: 0.82, maintenance_priority: "P1", recommended_actions: [{ action: "Initiate controlled shutdown — bearing failure risk imminent",      priority: "P1", sop_reference: "SOP-EMERGENCY-001 §3.1"  }, { action: "Flush lubrication system — check inline oil filter",                    priority: "P1", sop_reference: "SOP-LUBRICATION-001 §2.1" }], confidence_score: 0.91, work_order_id: "WO-20260614-0003", approved: false },
  { id: 2, timestamp: "2026-06-14T07:42:00", equipment_id: "Conveyor-B",    location: "Raw Material Yard", alert_level: "WARNING",   diagnosis: "Elevated vibration 0.52 mm/s on drive pulley bearings — Zone C per ISO 10816-3", root_cause: "Bearing wear — vibration dominant without significant temperature rise",                        health_score: 70, rul_days: 18.2, failure_probability: 0.31, maintenance_priority: "P2", recommended_actions: [{ action: "Vibration spectrum analysis (BPFI/BPFO) to isolate dominant frequency", priority: "P2", sop_reference: "SOP-VIBRATION-001 §2"   }, { action: "Schedule bearing replacement within RUL window (18 days)",               priority: "P2", sop_reference: "SOP-BEARING-001 §4.3"    }], confidence_score: 0.82, work_order_id: "WO-20260614-0002", approved: false },
  { id: 4, timestamp: "2026-06-14T09:30:00", equipment_id: "Blast-Furnace", location: "Blast Furnace #1",  alert_level: "CRITICAL", diagnosis: "Anomaly detected — vibration 0.58 mm/s and motor current 16.8 A above nominal limits", root_cause: "Tuyere assembly vibration signature indicates mechanical wear",                                 health_score: 55, rul_days: 6.1,  failure_probability: 0.71, maintenance_priority: "P1", recommended_actions: [{ action: "FFT vibration spectrum analysis — isolate bearing fault signature",       priority: "P1", sop_reference: "SOP-VIBRATION-001 §2.2"  }, { action: "Inspect tuyere assembly and blowpipe seal for wear",                    priority: "P1", sop_reference: "SOP-BF-001 §5.1"         }], confidence_score: 0.87, work_order_id: "WO-20260614-0004", approved: false },
  { id: 1, timestamp: "2026-06-14T06:15:00", equipment_id: "Pump-A",        location: "Blast Furnace #2",  alert_level: "NORMAL",   diagnosis: "Normal operation — all sensors within nominal envelope",                        root_cause: "No significant fault detected",                                                                 health_score: 84, rul_days: 62,   failure_probability: 0.08, maintenance_priority: "P3", recommended_actions: [{ action: "Continue routine monitoring per scheduled maintenance plan",         priority: "Routine", sop_reference: "PM-GUIDE-001 §4" }],                                                                          confidence_score: 0.79, work_order_id: "WO-20260614-0001", approved: true, approval_engineer: "Meena Sharma", approval_timestamp: "2026-06-14T06:30:00" },
];

// ─── Spare Parts Tab ──────────────────────────────────────────────────────────
function SparePartsTab() {
  const [parts, setParts]     = useState<SparePart[]>([]);
  const [summary, setSummary] = useState({ total: 0, in_stock: 0, low_stock: 0, out_of_stock: 0, max_lead_time_days: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState("ALL");
  const [search, setSearch]   = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/spare-parts");
      if (!res.ok) throw new Error();
      const data = await res.json();
      setParts(data.parts || []);
      setSummary(data.summary || {});
    } catch {
      setParts([
        { part_id: "SP-001", part_name: "Bearing Kit (SKF 6205)",      equipment_ids: ["Pump-A","Pump-B","Pump-C"], qty: 4,  unit: "sets",  status: "In Stock",     supplier: "Central Store",  lead_time_days: 0,  cost_inr: 18500  },
        { part_id: "SP-002", part_name: "Mechanical Seal (Type-II)",    equipment_ids: ["Pump-B"],                  qty: 1,  unit: "set",   status: "Low Stock",    supplier: "SAIL Stores",    lead_time_days: 4,  cost_inr: 32000  },
        { part_id: "SP-003", part_name: "Impeller (316 SS)",            equipment_ids: ["Pump-B"],                  qty: 0,  unit: "pc",    status: "Out of Stock", supplier: "Kirloskar OEM",  lead_time_days: 18, cost_inr: 95000  },
        { part_id: "SP-007", part_name: "Drive Chain (80H)",            equipment_ids: ["Conveyor-B"],              qty: 0,  unit: "set",   status: "Out of Stock", supplier: "Rexnord OEM",    lead_time_days: 12, cost_inr: 28000  },
        { part_id: "SP-014", part_name: "Mill Coupling Spindle",        equipment_ids: ["Rolling-Mill"],            qty: 0,  unit: "pc",    status: "Out of Stock", supplier: "Danieli OEM",    lead_time_days: 30, cost_inr: 420000 },
        { part_id: "SP-017", part_name: "Blowpipe Seal (Hi-Temp)",      equipment_ids: ["Blast-Furnace"],           qty: 0,  unit: "set",   status: "Out of Stock", supplier: "Paul Wurth OEM", lead_time_days: 21, cost_inr: 38000  },
        { part_id: "SP-006", part_name: "Conveyor Belt Section (5m)",   equipment_ids: ["Conveyor-B"],              qty: 2,  unit: "rolls", status: "In Stock",     supplier: "Central Store",  lead_time_days: 0,  cost_inr: 42000  },
        { part_id: "SP-013", part_name: "Roll Bearing (4-Row Tapered)", equipment_ids: ["Rolling-Mill"],            qty: 2,  unit: "sets",  status: "In Stock",     supplier: "SKF India",      lead_time_days: 0,  cost_inr: 185000 },
      ]);
      setSummary({ total: 8, in_stock: 3, low_stock: 1, out_of_stock: 4, max_lead_time_days: 30 });
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const filtered = parts.filter(p => {
    const matchStatus = filter === "ALL" || p.status === filter;
    const matchSearch = !search || p.part_name.toLowerCase().includes(search.toLowerCase()) ||
      p.equipment_ids.some(e => e.toLowerCase().includes(search.toLowerCase())) ||
      p.supplier.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const criticalParts = parts.filter(p => p.status === "Out of Stock" && p.lead_time_days > 14);

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Parts",  value: summary.total,        color: "#111827" },
          { label: "In Stock",     value: summary.in_stock,     color: "#166534" },
          { label: "Low Stock",    value: summary.low_stock,    color: "#92400e" },
          { label: "Out of Stock", value: summary.out_of_stock, color: "#991b1b" },
        ].map(s => (
          <div key={s.label} style={{ background: "#fff", borderRadius: 12, padding: "16px 20px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: s.color }}>{loading ? "—" : s.value}</div>
          </div>
        ))}
      </div>

      {criticalParts.length > 0 && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: "14px 18px", marginBottom: 16, display: "flex", gap: 12, alignItems: "flex-start" }}>
          <AlertTriangle size={16} style={{ color: "#dc2626", flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#111827", marginBottom: 4 }}>
              Emergency Procurement Required — {criticalParts.length} critical part{criticalParts.length > 1 ? "s" : ""} out of stock with long lead time
            </div>
            <div style={{ fontSize: 11, color: "#6b7280" }}>
              {criticalParts.map(p => `${p.part_name} (${p.lead_time_days}d lead — ${p.supplier})`).join(" · ")}
            </div>
          </div>
        </div>
      )}

      <div style={{ background: "#fff", borderRadius: 12, padding: "12px 16px", marginBottom: 16, display: "flex", alignItems: "center", gap: 12, border: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", gap: 4 }}>
          {["ALL", "In Stock", "Low Stock", "Out of Stock"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{ padding: "5px 12px", borderRadius: 8, fontSize: 11, fontWeight: 600, cursor: "pointer", border: "none",
                background: filter === f ? "#111827" : "#f8fafc", color: filter === f ? "#fff" : "#6b7280" }}>
              {f}
            </button>
          ))}
        </div>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search part name, equipment, or supplier…"
          style={{ flex: 1, fontSize: 12, padding: "6px 12px", borderRadius: 8, border: "1px solid #e5e7eb", background: "#f8fafc", color: "#111827", outline: "none" }} />
        <button onClick={load} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, fontWeight: 600, padding: "6px 12px", borderRadius: 8, border: "1px solid #e5e7eb", background: "#f8fafc", color: "#6b7280", cursor: "pointer" }}>
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f9fafb" }}>
              {["Part ID","Part Name","Equipment","Qty","Status","Supplier","Lead Time","Unit Cost","Procurement Impact"].map(h => (
                <th key={h} style={{ padding: "10px 14px", fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#6b7280", textAlign: "left", borderBottom: "1px solid #e5e7eb" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => {
              const st = STATUS_STYLE[p.status] || STATUS_STYLE["In Stock"];
              const isUrgent = p.status === "Out of Stock" && p.lead_time_days > 7;
              return (
                <tr key={p.part_id} style={{ borderBottom: "1px solid #f1f5f9", background: isUrgent ? "#fffbeb" : "transparent" }}>
                  <td style={{ padding: "10px 14px", fontSize: 11, fontFamily: "monospace", color: "#6b7280" }}>{p.part_id}</td>
                  <td style={{ padding: "10px 14px", fontSize: 12, fontWeight: 600, color: "#111827" }}>{p.part_name}</td>
                  <td style={{ padding: "10px 14px" }}>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                      {p.equipment_ids.map(e => (
                        <span key={e} style={{ fontSize: 9, fontWeight: 700, padding: "2px 6px", borderRadius: 4, background: "#eff6ff", color: "#1d4ed8", border: "1px solid #bfdbfe" }}>{e}</span>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 12, fontWeight: 700, color: p.qty === 0 ? "#dc2626" : "#111827" }}>{p.qty} {p.unit}</td>
                  <td style={{ padding: "10px 14px" }}>
                    <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 9px", borderRadius: 20, background: st.bg, color: st.text, border: `1px solid ${st.border}` }}>{p.status}</span>
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: "#374151" }}>{p.supplier}</td>
                  <td style={{ padding: "10px 14px", fontSize: 12, fontWeight: 700, color: p.lead_time_days === 0 ? "#166534" : p.lead_time_days > 14 ? "#dc2626" : "#92400e" }}>
                    {p.lead_time_days === 0 ? "Warehouse" : `${p.lead_time_days} days`}
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 12, color: "#111827" }}>{fmtINR(p.cost_inr)}</td>
                  <td style={{ padding: "10px 14px" }}>
                    {p.status === "Out of Stock" && p.lead_time_days > 14
                      ? <span style={{ fontSize: 10, fontWeight: 700, color: "#dc2626" }}>⚠ Order immediately</span>
                      : p.status === "Out of Stock"
                      ? <span style={{ fontSize: 10, fontWeight: 700, color: "#d97706" }}>↑ Raise PO now</span>
                      : p.status === "Low Stock"
                      ? <span style={{ fontSize: 10, fontWeight: 700, color: "#92400e" }}>→ Reorder soon</span>
                      : <span style={{ fontSize: 10, color: "#166534" }}>✓ Available</span>
                    }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div style={{ padding: "40px", textAlign: "center", color: "#9ca3af", fontSize: 13 }}>No parts match the current filter.</div>
        )}
      </div>
    </div>
  );
}

// ─── Feedback Panel ───────────────────────────────────────────────────────────
function FeedbackPanel() {
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  useEffect(() => {
    apiFetch("/api/feedback/stats").then(r => r.ok ? r.json() : null).then(d => { if (d) setStats(d); }).catch(() => {});
  }, []);

  if (!stats) return null;
  const total        = stats.total || 0;
  const confirmedPct = total ? Math.round((stats.confirmed / total) * 100) : 0;

  return (
    <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb", padding: "18px 22px", marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 4 }}>AI Feedback Loop</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>Engineer Feedback — Driving Model Improvement</div>
        </div>
        {total > 0 && <div style={{ fontSize: 10, color: "#6b7280" }}>Last: {stats.latest_timestamp?.slice(0, 16).replace("T", " ")}</div>}
      </div>
      {total === 0 ? (
        <div style={{ fontSize: 12, color: "#9ca3af", textAlign: "center", padding: "12px 0" }}>
          No feedback submitted yet — use thumbs up/down in AI Copilot to improve recommendations
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12 }}>
          {[
            { label: "Total Feedback", value: total,               icon: <ClipboardList size={14} />, color: "#111827" },
            { label: "Confirmed ✓",    value: stats.confirmed,     icon: <ThumbsUp size={14} />,      color: "#166534" },
            { label: "Corrected ✗",    value: stats.corrected,     icon: <ThumbsDown size={14} />,    color: "#991b1b" },
            { label: "RAG-Augmented",  value: stats.rag_augmented, icon: <Package size={14} />,       color: "#1d4ed8" },
          ].map(({ label, value, icon, color }) => (
            <div key={label} style={{ background: "#f9fafb", borderRadius: 8, padding: "12px 14px", border: "1px solid #e5e7eb" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#6b7280", marginBottom: 6 }}>{icon}<span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>{label}</span></div>
              <div style={{ fontSize: 22, fontWeight: 800, color }}>{value}</div>
            </div>
          ))}
        </div>
      )}
      {total > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "#6b7280" }}>Diagnostic accuracy (engineer-confirmed)</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: confirmedPct >= 80 ? "#166534" : "#92400e" }}>{confirmedPct}%</span>
          </div>
          <div style={{ height: 6, background: "#f1f5f9", borderRadius: 99, overflow: "hidden" }}>
            <div style={{ height: 6, width: `${confirmedPct}%`, background: confirmedPct >= 80 ? "#22c55e" : "#f59e0b", borderRadius: 99, transition: "width 0.8s ease" }} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Logbook Tab ──────────────────────────────────────────────────────────────
function LogbookTab({
  entries, spareParts, loading, lastSync, onRefresh,
}: {
  entries:    LogEntry[];
  spareParts: SparePart[];
  loading:    boolean;
  lastSync:   string;
  onRefresh:  () => void;
}) {
  const [filter, setFilter]     = useState("ALL");
  const [search, setSearch]     = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggleExpand = (id: number) =>
    setExpanded(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const filtered = entries.filter(e => {
    const lvl  = filter === "ALL" || e.alert_level === filter;
    const term = !search || e.equipment_id.toLowerCase().includes(search.toLowerCase()) ||
      (e.work_order_id || "").toLowerCase().includes(search.toLowerCase()) ||
      e.diagnosis.toLowerCase().includes(search.toLowerCase());
    return lvl && term;
  });

  const partsAtRisk = (eqId: string) =>
    spareParts.filter(p => p.equipment_ids.includes(eqId) && p.status !== "In Stock");

  return (
    <div>
      <FeedbackPanel />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Entries",        value: entries.length,                                                                                              color: "#111827" },
          { label: "Critical / Emergency", value: entries.filter(e => e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY").length,                   color: "#dc2626" },
          { label: "Pending Approval",     value: entries.filter(e => !e.approved).length,                                                                     color: "#d97706" },
          { label: "Approved",             value: entries.filter(e => e.approved).length,                                                                      color: "#166534" },
        ].map(s => (
          <div key={s.label} style={{ background: "#fff", borderRadius: 12, padding: "16px 20px", border: "1px solid #e5e7eb" }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: s.color }}>{loading ? "—" : s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: "#fff", borderRadius: 12, padding: "12px 16px", marginBottom: 16, display: "flex", alignItems: "center", gap: 12, border: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", gap: 4 }}>
          {["ALL","CRITICAL","WARNING","NORMAL"].map(l => (
            <button key={l} onClick={() => setFilter(l)}
              style={{ padding: "5px 12px", borderRadius: 8, fontSize: 11, fontWeight: 600, border: "none", cursor: "pointer",
                background: filter === l ? "#111827" : "#f8fafc", color: filter === l ? "#fff" : "#6b7280" }}>{l}</button>
          ))}
        </div>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search by equipment, work order ID, or diagnosis…"
          style={{ flex: 1, fontSize: 12, padding: "6px 12px", borderRadius: 8, border: "1px solid #e5e7eb", background: "#f8fafc", color: "#111827", outline: "none" }} />
        <button onClick={onRefresh}
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, fontWeight: 600, padding: "6px 12px", borderRadius: 8, border: "1px solid #e5e7eb", background: "#f8fafc", color: "#6b7280", cursor: "pointer" }}>
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          {lastSync ? `Synced ${lastSync}` : "Refresh"}
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {filtered.map(entry => {
          const isOpen      = expanded.has(entry.id);
          const risks       = partsAtRisk(entry.equipment_id);
          const hasPartRisk = risks.length > 0;
          return (
            <div key={entry.id} style={{ background: "#fff", borderRadius: 12, overflow: "hidden", border: "1px solid #e5e7eb" }}>
              <button onClick={() => toggleExpand(entry.id)}
                style={{ width: "100%", padding: "12px 18px", display: "flex", alignItems: "center", gap: 14, textAlign: "left", background: "none", border: "none", cursor: "pointer" }}>
                {entry.auto_logged && <Zap size={12} style={{ color: "#f59e0b", flexShrink: 0 }} />}
                <span style={{ width: 8, height: 8, borderRadius: "50%", flexShrink: 0, background: entry.approved ? "#10b981" : "#f59e0b" }} />
                <span style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 700, color: "#2563eb", flexShrink: 0, width: 160 }}>{entry.work_order_id || `WO-${entry.id}`}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#111827", flexShrink: 0, width: 110 }}>{entry.equipment_id}</span>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border shrink-0 ${ALERT_BADGE[entry.alert_level] || ALERT_BADGE.NORMAL}`}>{entry.alert_level}</span>
                <span className={`text-[9px] font-bold px-2 py-0.5 rounded shrink-0 ${PRIORITY_BADGE[entry.maintenance_priority] || PRIORITY_BADGE.Routine}`}>{entry.maintenance_priority}</span>
                {hasPartRisk && (
                  <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 4, background: "#fef3c7", color: "#92400e", border: "1px solid #fde68a", flexShrink: 0 }}>
                    {risks.filter(r => r.status === "Out of Stock").length > 0 ? "⚠ Parts OOS" : "↑ Parts Low"}
                  </span>
                )}
                <span style={{ flex: 1, fontSize: 12, color: "#6b7280", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{entry.diagnosis}</span>
                <span style={{ fontSize: 12, fontWeight: 700, flexShrink: 0, color: hc(entry.health_score) }}>{entry.health_score.toFixed(0)}%</span>
                <span style={{ fontSize: 10, fontWeight: 600, flexShrink: 0, color: entry.approved ? "#16a34a" : "#d97706", display: "flex", alignItems: "center", gap: 4 }}>
                  {entry.approved ? <CheckCircle2 size={13} /> : <Clock size={13} />}
                  {entry.approved ? "Approved" : "Pending"}
                </span>
                <span style={{ fontSize: 10, fontFamily: "monospace", color: "#c7c7cc", flexShrink: 0 }}>{entry.timestamp.replace("T"," ").slice(0,16)}</span>
                {isOpen ? <ChevronUp size={15} style={{ color: "#c7c7cc", flexShrink: 0 }} /> : <ChevronDown size={15} style={{ color: "#c7c7cc", flexShrink: 0 }} />}
              </button>

              {isOpen && (
                <div style={{ padding: "14px 18px 18px", borderTop: "1px solid #f1f5f9" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 6 }}>Diagnosis</div>
                      <div style={{ fontSize: 12, color: "#111827", lineHeight: 1.6, marginBottom: 10 }}>{entry.diagnosis}</div>
                      {entry.root_cause && entry.root_cause !== "No significant fault detected" && (
                        <>
                          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 6 }}>Root Cause</div>
                          <div style={{ fontSize: 12, color: "#374151", lineHeight: 1.6 }}>{entry.root_cause}</div>
                        </>
                      )}
                      {risks.length > 0 && (
                        <div style={{ marginTop: 12, background: "#fef3c7", border: "1px solid #fde68a", borderRadius: 8, padding: "10px 12px" }}>
                          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#92400e", marginBottom: 6 }}>Parts Status</div>
                          {risks.map(r => (
                            <div key={r.part_id} style={{ fontSize: 11, color: "#111827", marginBottom: 3 }}>
                              <span style={{ fontWeight: 600 }}>{r.part_name}</span>
                              <span style={{ color: r.status === "Out of Stock" ? "#dc2626" : "#d97706" }}> — {r.status}</span>
                              {r.lead_time_days > 0 && <span style={{ color: "#6b7280" }}> ({r.lead_time_days}d lead · {r.supplier})</span>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 8 }}>Recommended Actions</div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {(entry.recommended_actions || []).slice(0, 4).map((a, i) => (
                          <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12 }}>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 ${PRIORITY_BADGE[a.priority] || PRIORITY_BADGE.Routine}`}>{a.priority}</span>
                            <span style={{ flex: 1, color: "#374151" }}>{a.action}</span>
                            <span style={{ fontSize: 10, fontFamily: "monospace", color: "#d1d5db", flexShrink: 0 }}>{a.sop_reference}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 8 }}>Health Metrics</div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
                          {[
                            { label: "Health", val: `${entry.health_score.toFixed(0)}%`, color: hc(entry.health_score) },
                            { label: "RUL",    val: `${(entry.rul_days ?? 0).toFixed(1)}d`, color: (entry.rul_days ?? 99) < 7 ? "#ef4444" : "#f59e0b" },
                            { label: "Risk",   val: `${Math.round((entry.failure_probability || 0) * 100)}%`, color: rc(entry.failure_probability || 0) },
                          ].map(m => (
                            <div key={m.label} style={{ borderRadius: 8, padding: "8px 10px", textAlign: "center", border: "1px solid #e5e7eb" }}>
                              <div style={{ fontSize: 9, color: "#9ca3af", marginBottom: 3 }}>{m.label}</div>
                              <div style={{ fontSize: 15, fontWeight: 700, color: "#111827" }}>{m.val}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 6 }}>Approval Status</div>
                        {entry.approved ? (
                          <div style={{ fontSize: 12 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, color: "#16a34a" }}><CheckCircle2 size={14} /> Approved</div>
                            {entry.approval_engineer   && <div style={{ color: "#6b7280", marginTop: 2 }}>By: {entry.approval_engineer}</div>}
                            {entry.approval_notes      && <div style={{ color: "#374151", marginTop: 2, fontStyle: "italic" }}>&ldquo;{entry.approval_notes}&rdquo;</div>}
                            {entry.approval_timestamp  && <div style={{ color: "#9ca3af" }}>{entry.approval_timestamp.replace("T"," ").slice(0,16)}</div>}
                          </div>
                        ) : (
                          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: "#d97706" }}><Clock size={14} /> Awaiting engineer approval</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Approvals Tab ────────────────────────────────────────────────────────────
function ApprovalsTab({
  entries, setEntries, spareParts,
}: {
  entries:    LogEntry[];
  setEntries: Dispatch<SetStateAction<LogEntry[]>>;
  spareParts: SparePart[];
}) {
  const [engineer, setEngineer]     = useState("Lead Engineer");
  const [notes, setNotes]           = useState<Record<string, string>>({});
  const [processing, setProcessing] = useState<Set<string>>(new Set());
  const [history, setHistory]       = useState<HistoryItem[]>([]);

  const pending    = entries.filter(e => !e.approved && (e.maintenance_priority === "P1" || e.maintenance_priority === "P2"));
  const partsForEq = (eqId: string) => spareParts.filter(p => p.equipment_ids.includes(eqId) && (p.status === "Out of Stock" || p.status === "Low Stock"));

  const act = async (entry: LogEntry, approved: boolean) => {
    const woId = entry.work_order_id || `WO-${entry.id}`;
    setProcessing(prev => new Set([...prev, woId]));

    try {
      const p = new URLSearchParams({ approved: String(approved), engineer, notes: notes[woId] || "" });
      await apiFetch(`/api/approvals/${woId}?${p}`, 5000, { method: "POST" });
    } catch { }

    const ts = new Date().toISOString();

    setEntries(prev => prev.map(e =>
      e.id === entry.id
        ? { ...e, approved, approval_engineer: engineer, approval_timestamp: ts, approval_notes: notes[woId] || "" }
        : e
    ));

    setHistory(prev => [{
      woId,
      equipmentId: entry.equipment_id,
      decision:    approved ? "approved" : "rejected",
      engineer,
      timestamp:   ts,
      notes:       notes[woId] || undefined,
    }, ...prev]);

    setProcessing(prev => { const n = new Set(prev); n.delete(woId); return n; });
  };

  return (
    <div>
      <div style={{ background: "#fff", borderRadius: 12, padding: "14px 18px", marginBottom: 20, display: "flex", alignItems: "center", gap: 14, border: "1px solid #e5e7eb" }}>
        <User size={16} style={{ color: "#2563eb" }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "#111827", flexShrink: 0 }}>Approving as</span>
        <input value={engineer} onChange={e => setEngineer(e.target.value)}
          style={{ padding: "7px 12px", borderRadius: 8, fontSize: 13, fontWeight: 600, border: "1px solid #e5e7eb", background: "#f8fafc", color: "#111827", width: 220, outline: "none" }} />
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 16, fontSize: 13 }}>
          <span style={{ fontWeight: 600, color: "#d97706" }}>{pending.length} pending</span>
          {history.length > 0 && <span style={{ fontWeight: 600, color: "#16a34a" }}>{history.length} actioned this session</span>}
        </div>
      </div>

      {pending.length === 0 && history.length === 0 ? (
        <div style={{ background: "#fff", borderRadius: 12, padding: "48px", textAlign: "center", border: "1px solid #e5e7eb" }}>
          <ShieldCheck size={32} style={{ color: "#10b981", margin: "0 auto 12px" }} />
          <div style={{ fontSize: 14, fontWeight: 600, color: "#111827" }}>All clear — no pending approvals</div>
          <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 4 }}>All P1/P2 work orders have been reviewed</div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {pending.map(entry => {
            const woId   = entry.work_order_id || `WO-${entry.id}`;
            const busy   = processing.has(woId);
            const isCrit = entry.alert_level === "CRITICAL" || entry.alert_level === "EMERGENCY";
            const risks  = partsForEq(entry.equipment_id);
            const hasOOS = risks.some(r => r.status === "Out of Stock");

            return (
              <div key={woId} style={{ background: "#fff", borderRadius: 16, overflow: "hidden", border: "1px solid #e5e7eb", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}>
                <div style={{ height: 4, background: isCrit ? "#ef4444" : "#f59e0b" }} />
                <div style={{ padding: 20 }}>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" as const }}>
                        <span style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 700, color: "#2563eb" }}>{woId}</span>
                        {entry.auto_logged && (
                          <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 4, background: "#fef3c7", color: "#92400e", border: "1px solid #fde68a", display: "inline-flex", alignItems: "center", gap: 3 }}>
                            <Zap size={9} /> Auto-logged
                          </span>
                        )}
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${ALERT_BADGE[entry.alert_level] || ALERT_BADGE.NORMAL}`}>{entry.alert_level}</span>
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${PRIORITY_BADGE[entry.maintenance_priority] || PRIORITY_BADGE.Routine}`}>{entry.maintenance_priority}</span>
                        {hasOOS && <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 4, background: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca" }}>⚠ Parts OOS — order before scheduling</span>}
                      </div>
                      <div style={{ fontSize: 16, fontWeight: 700, color: "#111827" }}>{entry.equipment_id}</div>
                      <div style={{ fontSize: 12, color: "#6b7280" }}>{entry.location}</div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
                      {[
                        { label: "Health", val: `${entry.health_score.toFixed(0)}%`, color: hc(entry.health_score) },
                        { label: "RUL",    val: `${(entry.rul_days ?? 0).toFixed(1)}d`, color: (entry.rul_days ?? 99) < 7 ? "#ef4444" : "#f59e0b" },
                        { label: "Risk",   val: `${Math.round((entry.failure_probability || 0) * 100)}%`, color: rc(entry.failure_probability || 0) },
                      ].map(m => (
                        <div key={m.label} style={{ borderRadius: 8, padding: "10px 14px", textAlign: "center", border: "1px solid #e5e7eb", minWidth: 64 }}>
                          <div style={{ fontSize: 9, color: "#9ca3af", marginBottom: 3 }}>{m.label}</div>
                          <div style={{ fontSize: 16, fontWeight: 700, color: "#111827" }}>{m.val}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ fontSize: 14, color: "#111827", marginBottom: 10 }}>{entry.diagnosis}</div>
                  {entry.root_cause && entry.root_cause !== "No significant fault detected" && (
                    <div style={{ fontSize: 12, color: "#374151", background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, padding: "10px 12px", marginBottom: 10 }}>
                      <span style={{ fontWeight: 600 }}>Root cause: </span>{entry.root_cause}
                    </div>
                  )}

                  {risks.length > 0 && (
                    <div style={{ background: hasOOS ? "#fef2f2" : "#fef3c7", border: `1px solid ${hasOOS ? "#fecaca" : "#fde68a"}`, borderRadius: 8, padding: "10px 14px", marginBottom: 12 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: hasOOS ? "#991b1b" : "#92400e", marginBottom: 6 }}>
                        Procurement Alert — Parts Required
                      </div>
                      {risks.map(r => (
                        <div key={r.part_id} style={{ fontSize: 11, color: "#111827", marginBottom: 3 }}>
                          <span style={{ fontWeight: 600 }}>{r.part_name}</span>
                          <span style={{ color: r.status === "Out of Stock" ? "#dc2626" : "#d97706" }}> — {r.status}</span>
                          {r.lead_time_days > 0 && <span style={{ color: "#6b7280" }}> · {r.lead_time_days}d lead from {r.supplier} · {fmtINR(r.cost_inr)}</span>}
                        </div>
                      ))}
                    </div>
                  )}

                  {(entry.recommended_actions || []).length > 0 && (
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 8 }}>Required Actions</div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        {entry.recommended_actions.slice(0, 3).map((a, i) => (
                          <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12 }}>
                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 ${PRIORITY_BADGE[a.priority] || PRIORITY_BADGE.Routine}`}>{a.priority}</span>
                            <span style={{ flex: 1, color: "#374151" }}>{a.action}</span>
                            <span style={{ fontSize: 10, fontFamily: "monospace", color: "#d1d5db" }}>{a.sop_reference}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <textarea rows={2} value={notes[woId] || ""}
                    onChange={e => setNotes(prev => ({ ...prev, [woId]: e.target.value }))}
                    placeholder="Add conditions, observations, or instructions for the maintenance team…"
                    style={{ width: "100%", padding: "8px 12px", fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb", background: "#f9fafb", color: "#111827", outline: "none", resize: "none", marginBottom: 14, boxSizing: "border-box" as const }} />

                  <div style={{ display: "flex", gap: 12 }}>
                    <button onClick={() => act(entry, true)} disabled={busy}
                      style={{ flex: 1, padding: "11px", borderRadius: 12, background: "#111827", color: "#fff", fontSize: 13, fontWeight: 700, border: "none", cursor: busy ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, opacity: busy ? 0.5 : 1 }}>
                      <CheckCircle2 size={16} /> {busy ? "Processing…" : "Approve Work Order"}
                    </button>
                    <button onClick={() => act(entry, false)} disabled={busy}
                      style={{ flex: 1, padding: "11px", borderRadius: 12, background: "#fff", color: "#ef4444", fontSize: 13, fontWeight: 700, border: "1px solid #e5e7eb", cursor: busy ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, opacity: busy ? 0.5 : 1 }}>
                      <XCircle size={16} /> Reject
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Session history */}
          {history.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 10 }}>
                Approval History — This Session ({history.length})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {history.map((h, i) => (
                  <div key={i} style={{ background: "#fff", borderRadius: 10, padding: "12px 16px", border: "1px solid #e5e7eb", display: "flex", alignItems: "flex-start", gap: 12 }}>
                    {h.decision === "approved"
                      ? <CheckCircle2 size={16} style={{ color: "#10b981", flexShrink: 0, marginTop: 1 }} />
                      : <XCircle     size={16} style={{ color: "#ef4444", flexShrink: 0, marginTop: 1 }} />
                    }
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" as const }}>
                        <span style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 700, color: "#2563eb" }}>{h.woId}</span>
                        <span style={{ fontSize: 12, fontWeight: 600, color: "#111827" }}>{h.equipmentId}</span>
                        <span style={{ fontSize: 11, fontWeight: 700, color: h.decision === "approved" ? "#16a34a" : "#dc2626" }}>
                          {h.decision === "approved" ? "Approved" : "Rejected"}
                        </span>
                        <span style={{ fontSize: 11, color: "#6b7280" }}>by {h.engineer}</span>
                        <span style={{ marginLeft: "auto", fontSize: 10, fontFamily: "monospace", color: "#9ca3af" }}>
                          {h.timestamp.replace("T"," ").slice(0,16)}
                        </span>
                      </div>
                      {h.notes && (
                        <div style={{ fontSize: 11, color: "#374151", marginTop: 4, fontStyle: "italic" }}>&ldquo;{h.notes}&rdquo;</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function OpsPage() {
  const [entries, setEntries]       = useState<LogEntry[]>(SEED);
  const [spareParts, setSpareParts] = useState<SparePart[]>([]);
  const [loading, setLoading]       = useState(false);
  const [lastSync, setLastSync]     = useState("");
  const [tab, setTab]               = useState<"logbook" | "approvals" | "spares">("logbook");
  const fleet                       = useFleet();
  const autoLoggedRef               = useRef<Set<string>>(new Set());

  const loadData = async () => {
    setLoading(true);
    try {
      const [logRes, spRes] = await Promise.all([
        apiFetch("/api/logbook?limit=50"),
        apiFetch("/api/spare-parts"),
      ]);
      if (logRes.ok) { const d = await logRes.json(); if (d.entries?.length) setEntries(d.entries); }
      if (spRes.ok)  { const d = await spRes.json();  setSpareParts(d.parts || []); }
    } catch { }
    finally {
      setLoading(false);
      setLastSync(new Date().toLocaleTimeString());
    }
  };

  useEffect(() => { loadData(); const id = setInterval(loadData, 30000); return () => clearInterval(id); }, []);

  // Auto-log CRITICAL / EMERGENCY equipment from live fleet (once per equipment per session)
  useEffect(() => {
    fleet.forEach(asset => {
      const isCrit = asset.alert_level === "CRITICAL" || asset.alert_level === "EMERGENCY";
      if (!isCrit || autoLoggedRef.current.has(asset.equipment_id)) return;

      autoLoggedRef.current.add(asset.equipment_id);

      // Skip if an unresolved entry already exists for this equipment
      setEntries(prev => {
        if (prev.some(e => e.equipment_id === asset.equipment_id && !e.approved)) return prev;
        const ts   = new Date().toISOString();
        const rand = Math.floor(Math.random() * 9000) + 1000;
        const woId = `WO-AUTO-${ts.slice(0,10).replace(/-/g,"")}-${rand}`;
        return [{
          id:                   Date.now() + Math.floor(Math.random() * 1000),
          timestamp:            ts,
          equipment_id:         asset.equipment_id,
          location:             asset.location,
          alert_level:          asset.alert_level,
          diagnosis:            `⚡ Auto-detected ${asset.alert_level} — Health ${asset.health_score.toFixed(0)}%, failure risk ${Math.round(asset.failure_probability * 100)}%`,
          root_cause:           "Continuous sensor monitoring triggered alert threshold breach",
          health_score:         asset.health_score,
          rul_days:             asset.predicted_rul_days ?? 1,
          failure_probability:  asset.failure_probability,
          maintenance_priority: "P1",
          recommended_actions:  [
            { action: "Dispatch maintenance team immediately — threshold breached", priority: "P1", sop_reference: "SOP-ALERT-001 §2.1" },
            { action: "Notify shift supervisor and document incident",               priority: "P1", sop_reference: "SOP-OPS-001 §3.4"  },
          ],
          confidence_score:     0.90,
          work_order_id:        woId,
          approved:             false,
          auto_logged:          true,
        }, ...prev];
      });
    });
  }, [fleet]);

  const pendingCount = entries.filter(e => !e.approved && (e.maintenance_priority === "P1" || e.maintenance_priority === "P2")).length;

  const tabs = [
    { key: "logbook",   label: "Maintenance Logbook", icon: <ClipboardList size={15} />, badge: 0            },
    { key: "approvals", label: "Approvals",            icon: <ShieldCheck size={15} />,   badge: pendingCount },
    { key: "spares",    label: "Spare Parts",          icon: <Package size={15} />,       badge: 0            },
  ] as const;

  return (
    <div style={{ padding: "28px 36px", background: "#f8fafc", minHeight: "100vh" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: 3, color: "#6b7280", textTransform: "uppercase", marginBottom: 4 }}>Operations</div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: "#111827", margin: 0 }}>Maintenance Hub</h2>
        <p style={{ fontSize: 12, color: "#6b7280", margin: "4px 0 0" }}>
          Digital logbook, engineer approvals, spare parts inventory, and AI feedback loop — all in one place.
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 24, background: "#fff", borderRadius: 12, padding: 4, border: "1px solid #e5e7eb", width: "fit-content" }}>
        {tabs.map(({ key, label, icon, badge }) => (
          <button key={key} onClick={() => setTab(key as typeof tab)}
            style={{ display: "flex", alignItems: "center", gap: 7, padding: "8px 18px", borderRadius: 8, fontSize: 13, fontWeight: 600, border: "none", cursor: "pointer", transition: "all 0.15s",
              background: tab === key ? "#111827" : "transparent", color: tab === key ? "#fff" : "#6b7280" }}>
            {icon}{label}
            {badge > 0 && (
              <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 20, background: tab === key ? "rgba(255,255,255,0.2)" : "#f59e0b", color: "#fff" }}>{badge}</span>
            )}
          </button>
        ))}
      </div>

      {tab === "logbook"   && <LogbookTab   entries={entries} spareParts={spareParts} loading={loading} lastSync={lastSync} onRefresh={loadData} />}
      {tab === "approvals" && <ApprovalsTab entries={entries} setEntries={setEntries} spareParts={spareParts} />}
      {tab === "spares"    && <SparePartsTab />}
    </div>
  );
}
