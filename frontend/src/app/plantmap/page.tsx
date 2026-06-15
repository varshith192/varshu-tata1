"use client";

import { useRouter } from "next/navigation";
import { useFleet, FleetAsset } from "@/lib/fleetStore";
import { useEffect, useState } from "react";

const POSITIONS: Record<string, { cx: number; cy: number; r: number; label: string; short: string }> = {
  "Blast-Furnace": { cx: 160, cy: 220, r: 30, label: "Blast Furnace #1",       short: "BF-1"    },
  "Pump-B":        { cx: 270, cy: 105, r: 20, label: "BF Cooling Pump #3",     short: "Pump-B"  },
  "Pump-A":        { cx: 55,  cy: 105, r: 20, label: "BF Cooling Pump #2",     short: "Pump-A"  },
  "Pump-C":        { cx: 270, cy: 335, r: 20, label: "BF Cooling Pump #4",     short: "Pump-C"  },
  "Cooling-Unit":  { cx: 430, cy: 220, r: 22, label: "Steel Melting Cooler",   short: "SMS"     },
  "Rolling-Mill":  { cx: 590, cy: 130, r: 22, label: "Hot Rolling Mill",       short: "Mill"    },
  "Cooling-Fan-4": { cx: 590, cy: 320, r: 20, label: "Sinter Cooling Fan",     short: "Fan-4"   },
  "Conveyor-B":    { cx: 430, cy: 375, r: 20, label: "Raw Material Conveyor",  short: "Conv-B"  },
  "Compressor-2":  { cx: 750, cy: 120, r: 20, label: "O₂ Compressor",          short: "Comp-2"  },
  "Power-Unit":    { cx: 750, cy: 330, r: 20, label: "Power Distribution Unit",short: "Power"   },
};

const CONNECTIONS: [string, string, boolean?][] = [
  ["Pump-A",       "Blast-Furnace"],
  ["Pump-B",       "Blast-Furnace"],
  ["Pump-C",       "Blast-Furnace"],
  ["Blast-Furnace","Cooling-Unit"],
  ["Cooling-Unit", "Rolling-Mill"],
  ["Cooling-Unit", "Cooling-Fan-4"],
  ["Conveyor-B",   "Blast-Furnace", true],
  ["Compressor-2", "Blast-Furnace", true],
  ["Power-Unit",   "Cooling-Unit",  true],
  ["Rolling-Mill", "Compressor-2",  true],
];

const ZONES = [
  { x: 8,   y: 30,  w: 318, h: 400, label: "Blast Furnace Zone",    color: "#fff4f4" },
  { x: 336, y: 70,  w: 184, h: 360, label: "Steel Melting Zone",    color: "#f0f9ff" },
  { x: 530, y: 70,  w: 184, h: 360, label: "Rolling & Sinter Zone", color: "#f0fdf4" },
  { x: 724, y: 70,  w: 130, h: 320, label: "Utilities",             color: "#fafaf5" },
];

function healthColor(h: number, alert: string) {
  if (alert === "EMERGENCY") return "#dc2626";
  if (alert === "CRITICAL")  return "#ef4444";
  if (alert === "WARNING")   return "#f59e0b";
  return "#10b981";
}

function PulseRing({ cx, cy, r, color }: { cx: number; cy: number; r: number; color: string }) {
  const [scale, setScale] = useState(1);
  const [opacity, setOpacity] = useState(0.7);
  useEffect(() => {
    const id = setInterval(() => {
      setScale(s => s >= 1.7 ? 1 : s + 0.05);
      setOpacity(o => o <= 0.05 ? 0.7 : o - 0.04);
    }, 60);
    return () => clearInterval(id);
  }, []);
  return (
    <circle
      cx={cx} cy={cy}
      r={r * scale}
      fill="none"
      stroke={color}
      strokeWidth={2}
      opacity={opacity}
      style={{ pointerEvents: "none" }}
    />
  );
}

export default function PlantMapPage() {
  const fleet  = useFleet();
  const router = useRouter();
  const [hovered, setHovered] = useState<string | null>(null);

  const byId = Object.fromEntries(fleet.map(e => [e.equipment_id, e]));

  const critical = fleet.filter(e => e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY").length;
  const warning  = fleet.filter(e => e.alert_level === "WARNING").length;
  const avgHealth = fleet.length ? fleet.reduce((s, e) => s + e.health_score, 0) / fleet.length : 0;

  return (
    <div style={{ padding: "24px 32px", background: "#f8fafc", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 800, color: "#111827", margin: 0 }}>Plant Map</h2>
          <p style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>
            Live equipment health · Click any asset to open AI Copilot
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          {[
            { label: "Avg Health", value: `${avgHealth.toFixed(0)}%`, color: avgHealth < 60 ? "#ef4444" : avgHealth < 80 ? "#f59e0b" : "#10b981" },
            { label: "Critical",   value: critical,  color: "#ef4444" },
            { label: "Warning",    value: warning,   color: "#f59e0b" },
            { label: "Monitored", value: fleet.length, color: "#6366f1" },
          ].map((k, i) => (
            <div key={i} style={{ background: "#fff", borderRadius: 10, padding: "10px 18px", boxShadow: "0 1px 6px rgba(0,0,0,0.07)", textAlign: "center" }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>{k.label}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: k.color }}>{k.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* SVG Plant Map */}
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 2px 16px rgba(0,0,0,0.08)", padding: "16px", overflow: "hidden" }}>
        <svg viewBox="0 0 890 445" style={{ width: "100%", height: "auto", display: "block" }}>
          <defs>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
            </filter>
            <marker id="arrow" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#cbd5e1" />
            </marker>
            <marker id="arrowDot" markerWidth="6" markerHeight="6" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#a5b4fc" />
            </marker>
          </defs>

          {/* Zone backgrounds */}
          {ZONES.map(z => (
            <g key={z.label}>
              <rect x={z.x} y={z.y} width={z.w} height={z.h} rx={12} fill={z.color} stroke="#e5e7eb" strokeWidth={1} />
              <text x={z.x + z.w / 2} y={z.y + 18} textAnchor="middle" fontSize={9} fontWeight={700}
                fill="#9ca3af" letterSpacing={1.5} style={{ textTransform: "uppercase" }}>
                {z.label.toUpperCase()}
              </text>
            </g>
          ))}

          {/* Connection lines */}
          {CONNECTIONS.map(([from, to, isDotted]) => {
            const f = POSITIONS[from]; const t = POSITIONS[to];
            if (!f || !t) return null;
            return (
              <line key={`${from}-${to}`}
                x1={f.cx} y1={f.cy} x2={t.cx} y2={t.cy}
                stroke={isDotted ? "#a5b4fc" : "#cbd5e1"}
                strokeWidth={isDotted ? 1.5 : 2}
                strokeDasharray={isDotted ? "5,4" : undefined}
                markerEnd={isDotted ? "url(#arrowDot)" : "url(#arrow)"}
                opacity={0.7}
              />
            );
          })}

          {/* Equipment nodes */}
          {Object.entries(POSITIONS).map(([id, pos]) => {
            const asset = byId[id];
            if (!asset) return null;
            const col    = healthColor(asset.health_score, asset.alert_level);
            const isCrit = asset.alert_level === "CRITICAL" || asset.alert_level === "EMERGENCY";
            const isHov  = hovered === id;
            const health = Math.round(asset.health_score);
            const rul    = asset.predicted_rul_days?.toFixed(0) ?? "—";

            return (
              <g key={id}
                style={{ cursor: "pointer" }}
                onClick={() => router.push(`/console?eq=${id}`)}
                onMouseEnter={() => setHovered(id)}
                onMouseLeave={() => setHovered(null)}
                filter={isHov ? "url(#shadow)" : undefined}
              >
                {/* Pulse ring for critical */}
                {isCrit && <PulseRing cx={pos.cx} cy={pos.cy} r={pos.r + 4} color={col} />}

                {/* Outer health ring */}
                <circle cx={pos.cx} cy={pos.cy} r={pos.r + 6}
                  fill="none" stroke={col} strokeWidth={3} opacity={0.3} />

                {/* Main circle */}
                <circle cx={pos.cx} cy={pos.cy} r={pos.r}
                  fill={isHov ? "#f8fafc" : "#fff"}
                  stroke={col} strokeWidth={isHov ? 3 : 2.5}
                  style={{ transition: "all 0.2s" }}
                />

                {/* Health text inside */}
                <text x={pos.cx} y={pos.cy + (pos.r > 22 ? 5 : 4)} textAnchor="middle"
                  fontSize={pos.r > 22 ? 13 : 11} fontWeight={800} fill={col}>
                  {health}%
                </text>

                {/* Equipment short name */}
                <text x={pos.cx} y={pos.cy + pos.r + 16} textAnchor="middle"
                  fontSize={10} fontWeight={700} fill="#374151">
                  {pos.short}
                </text>

                {/* Alert badge */}
                {asset.alert_level !== "NORMAL" && (
                  <g>
                    <circle cx={pos.cx + pos.r - 1} cy={pos.cy - pos.r + 1} r={6}
                      fill={col} stroke="#fff" strokeWidth={1.5} />
                    <text x={pos.cx + pos.r - 1} y={pos.cy - pos.r + 4.5}
                      textAnchor="middle" fontSize={7} fontWeight={800} fill="#fff">
                      {asset.alert_level === "EMERGENCY" ? "!" : asset.alert_level === "CRITICAL" ? "!" : "~"}
                    </text>
                  </g>
                )}

                {/* Hover tooltip */}
                {isHov && (
                  <g>
                    <rect x={pos.cx - 68} y={pos.cy - pos.r - 62} width={136} height={54}
                      rx={8} fill="#1f2937" opacity={0.95} />
                    <text x={pos.cx} y={pos.cy - pos.r - 44} textAnchor="middle"
                      fontSize={10} fontWeight={700} fill="#f9fafb">
                      {pos.label}
                    </text>
                    <text x={pos.cx} y={pos.cy - pos.r - 29} textAnchor="middle"
                      fontSize={9} fill="#9ca3af">
                      Health {health}% · RUL {rul}d
                    </text>
                    <text x={pos.cx} y={pos.cy - pos.r - 16} textAnchor="middle"
                      fontSize={9} fontWeight={700}
                      fill={col}>
                      {asset.alert_level} · Click to diagnose →
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend only */}
      <div style={{ display: "flex", gap: 20, marginTop: 14, alignItems: "center", padding: "12px 16px", background: "#fff", borderRadius: 12, boxShadow: "0 1px 6px rgba(0,0,0,0.06)" }}>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, color: "#9ca3af", textTransform: "uppercase" }}>Legend</span>
        {[
          { color: "#ef4444", label: "Critical / Emergency" },
          { color: "#f59e0b", label: "Warning" },
          { color: "#10b981", label: "Normal" },
        ].map(l => (
          <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 16, height: 16, borderRadius: "50%", border: `3px solid ${l.color}`, background: "#fff" }} />
            <span style={{ fontSize: 12, color: "#374151" }}>{l.label}</span>
          </div>
        ))}
        <div style={{ width: 1, height: 20, background: "#e5e7eb", margin: "0 4px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width={28} height={8}><line x1={0} y1={4} x2={28} y2={4} stroke="#cbd5e1" strokeWidth={2} /></svg>
          <span style={{ fontSize: 11, color: "#6b7280" }}>Process flow</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <svg width={28} height={8}><line x1={0} y1={4} x2={28} y2={4} stroke="#a5b4fc" strokeWidth={1.5} strokeDasharray="4,3" /></svg>
          <span style={{ fontSize: 11, color: "#6b7280" }}>Utility supply</span>
        </div>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "#9ca3af" }}>Click any asset to open AI Copilot diagnostics</span>
      </div>
    </div>
  );
}
