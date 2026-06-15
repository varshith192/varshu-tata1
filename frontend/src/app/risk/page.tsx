"use client";

import { useFleet, FleetAsset } from "@/lib/fleetStore";

// ── Derive live sensor readings from health score (mirrors backend logic) ──
const SENSOR_NOMINAL = { temperature: 65, vibration: 0.25, pressure: 100, oil_temp: 52, motor_current: 13 };
const SENSOR_WARN    = { temperature: 78, vibration: 0.50, pressure: 88,  oil_temp: 65, motor_current: 16 };
const SENSOR_CRIT    = { temperature: 90, vibration: 0.70, pressure: 80,  oil_temp: 75, motor_current: 19 };
const SENSOR_UNITS   = { temperature: "°C", vibration: "mm/s", pressure: "PSI", oil_temp: "°C", motor_current: "A" };
const SENSOR_LABELS  = { temperature: "Temp", vibration: "Vibr", pressure: "Press", oil_temp: "Oil T", motor_current: "Current" };
type SensorKey = keyof typeof SENSOR_NOMINAL;
const SENSOR_KEYS: SensorKey[] = ["temperature", "vibration", "pressure", "oil_temp", "motor_current"];

function getSensorVal(eq: FleetAsset, key: SensorKey): number {
  const deg = (100 - eq.health_score) / 100;
  const seed = eq.equipment_id.charCodeAt(0) + key.length;
  const noise = (Math.sin(seed * 9301 + 49297) * 0.5 + 0.5) * 0.04 - 0.02;
  if (key === "pressure") return SENSOR_NOMINAL[key] - deg * 20 * (1 + noise);
  return SENSOR_NOMINAL[key] + deg * (SENSOR_CRIT[key] - SENSOR_NOMINAL[key]) * (0.85 + noise);
}

function sensorStatus(val: number, key: SensorKey): "crit" | "warn" | "ok" {
  const isLow = key === "pressure";
  if (isLow) return val < SENSOR_CRIT[key] ? "crit" : val < SENSOR_WARN[key] ? "warn" : "ok";
  return val >= SENSOR_CRIT[key] ? "crit" : val >= SENSOR_WARN[key] ? "warn" : "ok";
}

const STATUS_COLOR = { crit: "#fecaca", warn: "#fef08a", ok: "#bbf7d0" };
const STATUS_TEXT  = { crit: "#991b1b", warn: "#92400e", ok: "#166534" };

function exposureINR(e: FleetAsset) {
  const base = e.type === "pump" ? 3700000 : e.type === "conveyor" ? 1200000 : 700000;
  return e.failure_probability * base * Math.max(1, (100 - e.health_score) / 30);
}
function repairINR(e: FleetAsset) {
  const base = e.type === "pump" ? 480000 : e.type === "conveyor" ? 280000 : 180000;
  return base * (1 + (100 - e.health_score) / 100);
}
function fmtINR(v: number) {
  return v >= 10000000 ? `₹${(v / 10000000).toFixed(1)} Cr` : `₹${(v / 100000).toFixed(1)}L`;
}

export default function RiskAssessment() {
  const fleet = useFleet();
  const ranked = [...fleet].sort((a, b) => b.failure_probability - a.failure_probability);
  const atRisk = ranked.filter(e => e.alert_level !== "NORMAL");

  // Fleet pulse score
  const pulseScore = fleet.length
    ? Math.round(fleet.reduce((s, e) => s + e.failure_probability * 100, 0) / fleet.length)
    : 0;
  const pulseColor = pulseScore > 40 ? "#ef4444" : pulseScore > 20 ? "#f59e0b" : "#10b981";

  return (
    <div style={{ padding: "28px 36px", background: "#f8fafc", minHeight: "100vh" }}>
      <h2 style={{ fontSize: 28, fontWeight: 700, color: "#1d1d1f", marginBottom: 24 }}>Risk Assessment</h2>

      {/* ── Row 1: Fleet Pulse + Failure Timeline ── */}
      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 16, marginBottom: 20 }}>

        {/* Fleet Risk Pulse */}
        <div style={{ background: "#fff", borderRadius: 16, padding: "24px 20px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#aaa" }}>Fleet Risk Pulse</div>
          <div style={{ fontSize: 64, fontWeight: 900, color: pulseColor, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>{pulseScore}</div>
          <div style={{ fontSize: 11, color: "#6e6e73" }}>Avg failure probability %</div>
          <div style={{ width: "100%", height: 6, background: "#f1f5f9", borderRadius: 99, marginTop: 4 }}>
            <div style={{ height: 6, borderRadius: 99, background: pulseColor, width: `${pulseScore}%`, transition: "width 0.6s ease" }} />
          </div>
          <div style={{ fontSize: 10, color: "#aaa", marginTop: 4 }}>
            {pulseScore > 40 ? "⚠ High fleet risk" : pulseScore > 20 ? "↑ Elevated risk" : "✓ Fleet stable"}
          </div>
        </div>

        {/* Failure Timeline */}
        <div style={{ background: "#fff", borderRadius: 16, padding: "20px 24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#aaa", marginBottom: 4 }}>Predicted Failure Timeline</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#1d1d1f", marginBottom: 14 }}>Days until predicted failure — next 150 days</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
            {ranked.map(eq => {
              const rul = eq.predicted_rul_days ?? 150;
              const pct = Math.min(100, (rul / 150) * 100);
              const color = rul < 7 ? "#ef4444" : rul < 30 ? "#f59e0b" : "#10b981";
              return (
                <div key={eq.equipment_id} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: "#374151", width: 110, flexShrink: 0 }}>{eq.equipment_id}</span>
                  <div style={{ flex: 1, background: "#f1f5f9", borderRadius: 99, height: 12, position: "relative" }}>
                    <div style={{ width: `${pct}%`, height: 12, borderRadius: 99, background: color, transition: "width 0.6s ease" }} />
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 700, color, width: 44, textAlign: "right" }}>
                    {rul < 1 ? "<1d" : `${Math.round(rul)}d`}
                  </span>
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
            {[["#ef4444","< 7 days"],["#f59e0b","7–30 days"],["#10b981","30+ days"]].map(([c,l]) => (
              <div key={l} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <span style={{ width: 8, height: 8, borderRadius: 99, background: c, display: "inline-block" }} />
                <span style={{ fontSize: 10, color: "#6e6e73" }}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Row 2: Sensor Anomaly Heatmap ── */}
      <div style={{ background: "#fff", borderRadius: 16, padding: "20px 24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)", marginBottom: 20 }}>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#aaa", marginBottom: 4 }}>Multi-Sensor Intelligence</div>
        <div style={{ fontSize: 14, fontWeight: 700, color: "#1d1d1f", marginBottom: 16 }}>Live Sensor Anomaly Heatmap — All Equipment</div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "separate", borderSpacing: 3, minWidth: 700 }}>
            <thead>
              <tr>
                <th style={{ fontSize: 10, fontWeight: 700, color: "#aaa", textAlign: "left", paddingRight: 12, paddingBottom: 6 }}>Equipment</th>
                {SENSOR_KEYS.map(k => (
                  <th key={k} style={{ fontSize: 10, fontWeight: 700, color: "#6e6e73", textAlign: "center", paddingBottom: 6, minWidth: 80 }}>
                    {SENSOR_LABELS[k]}<br />
                    <span style={{ fontWeight: 400, color: "#aaa" }}>({SENSOR_UNITS[k]})</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranked.map(eq => (
                <tr key={eq.equipment_id}>
                  <td style={{ fontSize: 11, fontWeight: 700, color: "#111827", paddingRight: 12, paddingBottom: 3, whiteSpace: "nowrap" }}>
                    {eq.equipment_id}
                  </td>
                  {SENSOR_KEYS.map(key => {
                    const val = getSensorVal(eq, key);
                    const st  = sensorStatus(val, key);
                    return (
                      <td key={key} style={{ padding: "5px 4px", textAlign: "center" }}>
                        <div style={{
                          background: STATUS_COLOR[st], borderRadius: 6, padding: "4px 0",
                          fontSize: 11, fontWeight: 700, color: STATUS_TEXT[st],
                        }}>
                          {val.toFixed(key === "vibration" ? 2 : 1)}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ display: "flex", gap: 16, marginTop: 12 }}>
          {([["#fecaca","#991b1b","Critical"],["#fef08a","#92400e","Warning"],["#bbf7d0","#166534","Normal"]] as const).map(([bg,tc,l]) => (
            <div key={l} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 14, height: 14, borderRadius: 3, background: bg, display: "inline-block" }} />
              <span style={{ fontSize: 10, color: "#6e6e73" }}>{l}</span>
            </div>
          ))}
          <span style={{ fontSize: 10, color: "#aaa", marginLeft: "auto" }}>Updates every 3s</span>
        </div>
      </div>

      {/* ── Row 3: Repair vs Failure Cost ── */}
      <div style={{ background: "#fff", borderRadius: 16, padding: "20px 24px", boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#aaa", marginBottom: 4 }}>Maintenance ROI</div>
        <div style={{ fontSize: 14, fontWeight: 700, color: "#1d1d1f", marginBottom: 16 }}>Repair Now vs. Failure Cost — Act before failure to save</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {atRisk.slice(0, 6).map(eq => {
            const fail = exposureINR(eq);
            const fix  = repairINR(eq);
            const save = fail - fix;
            const max  = Math.max(fail, fix);
            return (
              <div key={eq.equipment_id} style={{ display: "grid", gridTemplateColumns: "120px 1fr 1fr 80px", gap: 12, alignItems: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#111827" }}>{eq.equipment_id}</span>
                <div>
                  <div style={{ fontSize: 9, color: "#aaa", marginBottom: 2 }}>Repair now: <strong style={{ color: "#111827" }}>{fmtINR(fix)}</strong></div>
                  <div style={{ height: 8, borderRadius: 99, background: "#f1f5f9" }}>
                    <div style={{ height: 8, borderRadius: 99, background: "#0071e3", width: `${(fix / max) * 100}%` }} />
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 9, color: "#aaa", marginBottom: 2 }}>If it fails: <strong style={{ color: "#111827" }}>{fmtINR(fail)}</strong></div>
                  <div style={{ height: 8, borderRadius: 99, background: "#f1f5f9" }}>
                    <div style={{ height: 8, borderRadius: 99, background: "#ef4444", width: `${(fail / max) * 100}%` }} />
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 9, color: "#aaa" }}>Save</div>
                  <div style={{ fontSize: 13, fontWeight: 800, color: save > 0 ? "#10b981" : "#ef4444" }}>{fmtINR(Math.abs(save))}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
