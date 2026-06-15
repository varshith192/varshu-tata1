"use client";

import { useEffect, useState } from "react";
import { useFleet, FleetAsset } from "@/lib/fleetStore";
import { AlertTriangle, ShieldAlert, Activity, Zap, TrendingDown, CheckCircle2, Clock } from "lucide-react";

function fmtCr(v: number) {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(2)} Cr`;
  if (v >= 100000)   return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${Math.round(v / 1000)}K`;
}

function revenueAtRisk(fleet: FleetAsset[]) {
  const VAL: Record<string, number> = { pump: 2500000, furnace: 8000000, conveyor: 1200000, mill: 6000000, fan: 800000 };
  return fleet.reduce((s, e) => s + e.failure_probability * (VAL[e.type] ?? 2000000), 0);
}

function getThreatLevel(critical: number, emergency: number) {
  if (emergency > 0 || critical >= 3) return "HIGH";
  if (critical >= 1) return "MEDIUM";
  return "LOW";
}

function calcOEE(fleet: FleetAsset[]) {
  const avgH = fleet.reduce((s, e) => s + e.health_score, 0) / (fleet.length || 1);
  const critF = 1 - fleet.filter(e => e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY").length * 0.04;
  return Math.min(99, avgH / 100 * 1.05) * Math.min(0.98, critF * 0.97) * 0.985 * 100;
}

const SENTINEL_FEED = [
  { type: "MAINTENANCE", pct: 87, text: "Maintenance plan: 1 immediate, 3 short-term actions",       asset: "Pump-B",        time: "now" },
  { type: "ESCALATION",  pct: 93, text: "Escalation triggered: level=CRITICAL",                       asset: "Blast-Furnace", time: "2m" },
  { type: "INVESTIGATE", pct: 81, text: "Auto-investigation: bearing thermal fatigue",                 asset: "Conveyor-B",    time: "5m" },
  { type: "ALERT",       pct: 76, text: "Alert: vibration 0.52 mm/s — Priority MEDIUM",               asset: "Rolling-Mill",  time: "8m" },
  { type: "MAINTENANCE", pct: 69, text: "Scheduled PM window computed: 14-day RUL buffer",            asset: "Cooling-Fan-4", time: "12m" },
];

const SENTINEL_COLORS: Record<string, string> = {
  MAINTENANCE: "#10b981",
  ESCALATION:  "#ef4444",
  INVESTIGATE: "#6366f1",
  ALERT:       "#f59e0b",
};

function LiveTicker({ value, fmt }: { value: number; fmt: (v: number) => string }) {
  const [disp, setDisp] = useState(value);
  useEffect(() => {
    const diff = value - disp, steps = 20, step = diff / steps;
    let n = 0;
    const t = setInterval(() => { setDisp(p => p + step); if (++n >= steps) clearInterval(t); }, 40);
    return () => clearInterval(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  return <span>{fmt(disp)}</span>;
}

export default function WarRoom() {
  const fleet     = useFleet();
  const [tick, setTick] = useState(0);
  useEffect(() => { const id = setInterval(() => setTick(t => t + 1), 3000); return () => clearInterval(id); }, []);

  const critical   = fleet.filter(e => e.alert_level === "CRITICAL").length;
  const emergency  = fleet.filter(e => e.alert_level === "EMERGENCY").length;
  const warning    = fleet.filter(e => e.alert_level === "WARNING").length;
  const normal     = fleet.filter(e => e.alert_level === "NORMAL").length;
  const critAll    = critical + emergency;
  const avgHealth  = fleet.reduce((s, e) => s + e.health_score, 0) / (fleet.length || 1);
  const revRisk    = revenueAtRisk(fleet);
  const threat     = getThreatLevel(critical, emergency);
  const oee        = calcOEE(fleet);

  const failIn7d   = fleet.filter(e => (e.predicted_rul_days ?? 999) <= 7).length;
  const failIn14d  = fleet.filter(e => (e.predicted_rul_days ?? 999) <= 14).length;
  const failIn30d  = fleet.filter(e => (e.predicted_rul_days ?? 999) <= 30).length;

  const critAssets = [...fleet]
    .filter(e => e.alert_level !== "NORMAL")
    .sort((a, b) => a.health_score - b.health_score);

  const countdown = [...fleet]
    .filter(e => (e.predicted_rul_days ?? 999) <= 30)
    .sort((a, b) => (a.predicted_rul_days ?? 999) - (b.predicted_rul_days ?? 999));

  const escalations = critAssets.slice(0, 5).map((e, i) => ({
    name: e.equipment_id,
    label: e.label,
    level: e.alert_level,
    roles: i < 2 ? "supervisor, reliability_engineer" : "plant_manager, supervisor",
  }));

  const THREAT_STYLE: Record<string, { bg: string; border: string; dot: string; text: string }> = {
    HIGH:   { bg: "#fef2f2", border: "#fecaca", dot: "#ef4444", text: "#dc2626" },
    MEDIUM: { bg: "#fffbeb", border: "#fde68a", dot: "#f59e0b", text: "#b45309" },
    LOW:    { bg: "#f0fdf4", border: "#bbf7d0", dot: "#10b981", text: "#065f46" },
  };
  const ts = THREAT_STYLE[threat];

  return (
    <div style={{ padding: "24px 32px", background: "#f8fafc", minHeight: "100vh" }}>

      {/* ── Threat level banner ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 800, color: "#111827", margin: 0 }}>War Room</h2>
          <p style={{ fontSize: 13, color: "#6b7280", marginTop: 3 }}>Executive Maintenance Command · Real-time</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ padding: "8px 20px", borderRadius: 10, background: ts.bg, border: `1.5px solid ${ts.border}`, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: ts.dot, display: "inline-block", boxShadow: `0 0 0 3px ${ts.dot}44` }} />
            <span style={{ fontSize: 13, fontWeight: 800, color: ts.text, letterSpacing: 1 }}>THREAT LEVEL: {threat}</span>
          </div>
          <div style={{ fontSize: 12, color: "#9ca3af" }}>
            Sentinel online · {127 + tick * 3} cycles · {10 + Math.min(tick, 8)} anomalies
          </div>
        </div>
      </div>

      {/* ── Row 1: Primary KPIs ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginBottom: 14 }}>
        {[
          { label: "Plant Health",       value: `${avgHealth.toFixed(0)}%`, color: avgHealth < 60 ? "#ef4444" : avgHealth < 80 ? "#f59e0b" : "#10b981", sub: `OEE ${oee.toFixed(1)}%` },
          { label: "Revenue at Risk",    value: fmtCr(revRisk),             color: "#ef4444",  sub: "Risk-weighted exposure" },
          { label: "Critical Assets",    value: critAll,                    color: "#ef4444",  sub: `${warning} warning, ${normal} normal` },
          { label: "Predicted Failures", value: failIn14d,                  color: "#f59e0b",  sub: "within 14 days" },
          { label: "AI Detections",      value: 10 + Math.min(tick, 8),     color: "#6366f1",  sub: "Sentinel autonomous scans" },
        ].map((k, i) => (
          <div key={i} style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 6 }}>{k.label}</div>
            <div style={{ fontSize: 28, fontWeight: 900, color: k.color, lineHeight: 1 }}>{k.value}</div>
            <div style={{ fontSize: 11, color: "#6b7280", marginTop: 5 }}>{k.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Row 2: Alert counts strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 10, marginBottom: 16 }}>
        {[
          { label: "Active Alerts",    value: critAll + warning,              dotColor: "#ef4444" },
          { label: "Critical Alerts",  value: critAll,                         dotColor: "#ef4444" },
          { label: "Escalations",      value: escalations.length,              dotColor: "#6366f1" },
          { label: "Sentinel Actions", value: SENTINEL_FEED.length,            dotColor: "#10b981" },
          { label: "Fail within 7d",  value: failIn7d,                        dotColor: failIn7d > 0 ? "#ef4444" : "#10b981" },
          { label: "Fail within 14d", value: failIn14d,                       dotColor: failIn14d > 0 ? "#f59e0b" : "#10b981" },
        ].map((k, i) => (
          <div key={i} style={{ background: "#fff", borderRadius: 12, padding: "12px 16px", boxShadow: "0 1px 6px rgba(0,0,0,0.06)", display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: k.dotColor, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#9ca3af" }}>{k.label}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "#111827", lineHeight: 1.1 }}>{k.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Row 3: Three columns ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 14 }}>

        {/* Critical Alerts */}
        <div style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>Critical Alerts</span>
            <span style={{ fontSize: 11, color: "#2563eb", fontWeight: 600, cursor: "pointer" }}>All Alerts →</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {critAssets.slice(0, 5).map(e => (
              <div key={e.equipment_id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 10, background: "#fef2f2", border: "1px solid #fecaca" }}>
                <AlertTriangle size={14} color="#ef4444" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#111827", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{e.equipment_id}</div>
                  <div style={{ fontSize: 10, color: "#6b7280" }}>{e.location}</div>
                </div>
                <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 20, background: e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY" ? "#fef2f2" : "#fffbeb", color: e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY" ? "#dc2626" : "#b45309", border: `1px solid ${e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY" ? "#fecaca" : "#fde68a"}`, whiteSpace: "nowrap" }}>
                  {e.alert_level}
                </span>
              </div>
            ))}
            {critAssets.length === 0 && (
              <div style={{ textAlign: "center", padding: "16px 0", color: "#10b981", fontSize: 12, fontWeight: 600 }}>
                <CheckCircle2 size={20} style={{ marginBottom: 4 }} />
                <div>All equipment normal</div>
              </div>
            )}
          </div>
        </div>

        {/* Sentinel Feed */}
        <div style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>Sentinel Feed</span>
            <span style={{ fontSize: 10, color: "#10b981", fontWeight: 600 }}>{SENTINEL_FEED.length} actions</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {SENTINEL_FEED.map((f, i) => {
              const col = SENTINEL_COLORS[f.type] ?? "#6b7280";
              return (
                <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: col, flexShrink: 0, marginTop: 4 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                      <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5, color: col }}>{f.type}</span>
                      <span style={{ fontSize: 9, color: "#9ca3af" }}>{f.time} ago</span>
                      <span style={{ marginLeft: "auto", fontSize: 9, fontWeight: 700, color: "#374151" }}>{f.pct}%</span>
                    </div>
                    <div style={{ fontSize: 11, color: "#374151", lineHeight: 1.4 }}>{f.text}</div>
                    <div style={{ fontSize: 10, color: "#9ca3af" }}>{f.asset}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Active Escalations */}
        <div style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>Active Escalations</span>
            <span style={{ fontSize: 10, color: "#ef4444", fontWeight: 700 }}>{escalations.length} active</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {escalations.map((e, i) => (
              <div key={i} style={{ padding: "9px 12px", borderRadius: 10, background: "#f8fafc", border: "1px solid #e5e7eb" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#111827" }}>{e.name}</span>
                  <span style={{ fontSize: 9, fontWeight: 700, padding: "1px 6px", borderRadius: 20, background: e.level === "CRITICAL" || e.level === "EMERGENCY" ? "#fef2f2" : "#fffbeb", color: e.level === "CRITICAL" || e.level === "EMERGENCY" ? "#dc2626" : "#b45309" }}>
                    {e.level}
                  </span>
                </div>
                <div style={{ fontSize: 10, color: "#6b7280" }}>{e.label}</div>
                <div style={{ fontSize: 9, color: "#9ca3af", marginTop: 3 }}>→ {e.roles}</div>
              </div>
            ))}
            {escalations.length === 0 && (
              <div style={{ textAlign: "center", padding: "16px 0", color: "#10b981", fontSize: 12 }}>No active escalations</div>
            )}
          </div>
        </div>
      </div>

      {/* ── Row 4: Failure Countdown + Downtime Risk + AI Recommendations ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>

        {/* Failure Countdown */}
        <div style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>Failure Countdown</span>
            <span style={{ fontSize: 10, color: "#ef4444", fontWeight: 700 }}>{failIn30d} within 30d</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {countdown.slice(0, 5).map(e => {
              const rul = e.predicted_rul_days ?? 0;
              const urgency = rul <= 7 ? "#ef4444" : rul <= 14 ? "#f59e0b" : "#6b7280";
              const urgLabel = rul <= 7 ? "Emergency within 7d" : rul <= 14 ? "Schedule within 14d" : "Plan within 30d";
              return (
                <div key={e.equipment_id} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 10, background: `${urgency}15`, border: `2px solid ${urgency}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <span style={{ fontSize: 13, fontWeight: 900, color: urgency }}>{rul.toFixed(0)}d</span>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#111827" }}>{e.equipment_id}</div>
                    <div style={{ fontSize: 10, color: urgency, fontWeight: 600 }}>{urgLabel}</div>
                  </div>
                  <div style={{ width: 60, height: 6, background: "#f1f5f9", borderRadius: 99 }}>
                    <div style={{ height: 6, borderRadius: 99, background: urgency, width: `${Math.min(100, (1 - rul / 30) * 100)}%` }} />
                  </div>
                </div>
              );
            })}
            {countdown.length === 0 && (
              <div style={{ textAlign: "center", padding: 16, color: "#10b981", fontSize: 12, fontWeight: 600 }}>
                No failures predicted within 30 days
              </div>
            )}
          </div>
        </div>

        {/* Downtime Risk Window */}
        <div style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", marginBottom: 12 }}>Downtime Risk Window</div>
          {[
            { label: "Next 7 days",  count: failIn7d,              risk: failIn7d / (fleet.length || 1)  },
            { label: "Next 14 days", count: failIn14d,             risk: failIn14d / (fleet.length || 1) },
            { label: "Next 30 days", count: failIn30d,             risk: failIn30d / (fleet.length || 1) },
          ].map(r => (
            <div key={r.label} style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: "#374151" }}>{r.label}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: r.count > 0 ? "#ef4444" : "#10b981" }}>{r.count} assets at risk</span>
              </div>
              <div style={{ height: 10, background: "#f1f5f9", borderRadius: 99, overflow: "hidden" }}>
                <div style={{ height: 10, borderRadius: 99, width: `${Math.min(100, r.risk * 100)}%`, background: r.count > 2 ? "#ef4444" : r.count > 0 ? "#f59e0b" : "#10b981", transition: "width 0.6s" }} />
              </div>
            </div>
          ))}
          <div style={{ marginTop: 8, paddingTop: 12, borderTop: "1px solid #f1f5f9" }}>
            <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#9ca3af", marginBottom: 8 }}>Fleet Status Breakdown</div>
            {[
              { label: "Critical / Emergency", count: critAll,  color: "#ef4444" },
              { label: "Warning",              count: warning,  color: "#f59e0b" },
              { label: "Normal",               count: normal,   color: "#10b981" },
            ].map(s => (
              <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: s.color, flexShrink: 0 }} />
                <span style={{ fontSize: 11, color: "#374151", flex: 1 }}>{s.label}</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#111827" }}>{s.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Recommendations */}
        <div style={{ background: "#fff", borderRadius: 14, padding: "16px 18px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>AI Recommendations</span>
            <Zap size={14} color="#6366f1" />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {critAssets.slice(0, 4).map((e, i) => {
              const rul   = e.predicted_rul_days ?? 0;
              const urgency = rul <= 7 ? "Schedule emergency maintenance within 24 hours" : rul <= 14 ? "Schedule maintenance within 72 hours" : "Plan preventive maintenance within 2 weeks";
              const col   = rul <= 7 ? "#ef4444" : rul <= 14 ? "#f59e0b" : "#6b7280";
              return (
                <div key={i} style={{ padding: "10px 12px", borderRadius: 10, background: `${col}08`, borderLeft: `3px solid ${col}` }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#111827", marginBottom: 2 }}>{urgency}</div>
                  <div style={{ fontSize: 10, color: "#6b7280" }}>
                    {e.equipment_id} · <span style={{ color: col, fontWeight: 700 }}>{rul.toFixed(0)}d RUL</span>
                  </div>
                </div>
              );
            })}
            {critAssets.length === 0 && (
              <div style={{ padding: "16px 0", textAlign: "center" }}>
                <CheckCircle2 size={24} color="#10b981" style={{ marginBottom: 8 }} />
                <div style={{ fontSize: 12, color: "#10b981", fontWeight: 600 }}>Fleet is healthy — no urgent actions</div>
              </div>
            )}
            <div style={{ paddingTop: 8, borderTop: "1px solid #f1f5f9", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              {[
                { label: "Fleet Health", val: `${avgHealth.toFixed(0)}%`, color: avgHealth < 60 ? "#ef4444" : "#10b981" },
                { label: "OEE",         val: `${oee.toFixed(1)}%`,        color: "#6366f1" },
                { label: "Exposure",    val: fmtCr(revRisk),              color: "#ef4444" },
              ].map(m => (
                <div key={m.label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 9, color: "#9ca3af", fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>{m.label}</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: m.color }}>{m.val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
