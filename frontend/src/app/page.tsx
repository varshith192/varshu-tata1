"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Activity, AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useFleet } from "@/lib/fleetStore";

// ─── Equipment list (Digital Twin) ──────────────────────────────
const EQUIPMENT_LIST = [
  { id: "Pump-B",       label: "Pump-B — Blast Furnace #3",        type: "pump",     base: { temperature: 92.5, vibration: 0.72, pressure: 84.0,  oil_temp: 68.5, motor_current: 18.2 } },
  { id: "Pump-A",       label: "Pump-A — Blast Furnace #2",        type: "pump",     base: { temperature: 71.0, vibration: 0.38, pressure: 98.0,  oil_temp: 56.0, motor_current: 14.2 } },
  { id: "Pump-C",       label: "Pump-C — Blast Furnace #4",        type: "pump",     base: { temperature: 66.0, vibration: 0.28, pressure: 102.0, oil_temp: 53.0, motor_current: 13.8 } },
  { id: "Conveyor-B",   label: "Conveyor-B — Raw Material Yard",   type: "conveyor", base: { temperature: 74.0, vibration: 0.52, pressure: 92.0,  oil_temp: 60.0, motor_current: 15.5 } },
  { id: "Cooling-Fan-4",label: "Cooling-Fan-4 — Sinter Plant",     type: "fan",      base: { temperature: 68.0, vibration: 0.31, pressure: 99.0,  oil_temp: 54.0, motor_current: 13.5 } },
  { id: "Rolling-Mill", label: "Rolling-Mill — Hot Rolling Section",type: "mill",    base: { temperature: 69.0, vibration: 0.32, pressure: 96.0,  oil_temp: 52.0, motor_current: 14.0 } },
  { id: "Cooling-Unit", label: "Cooling-Unit — Steel Melting Shop", type: "fan",     base: { temperature: 64.0, vibration: 0.29, pressure: 101.0, oil_temp: 50.0, motor_current: 12.8 } },
  { id: "Power-Unit",   label: "Power-Unit — Power Distribution",  type: "pump",     base: { temperature: 58.0, vibration: 0.22, pressure: 104.0, oil_temp: 47.0, motor_current: 11.5 } },
  { id: "Blast-Furnace",label: "Blast-Furnace — Blast Furnace #1", type: "furnace",  base: { temperature: 81.0, vibration: 0.58, pressure: 87.0,  oil_temp: 63.0, motor_current: 16.8 } },
  { id: "Compressor-2", label: "Compressor-2 — Oxygen Plant",      type: "pump",     base: { temperature: 67.0, vibration: 0.27, pressure: 103.0, oil_temp: 51.0, motor_current: 13.2 } },
];

const THRESHOLDS: Record<string, { warn: number; crit: number; unit: string; nominal: string }> = {
  temperature:    { warn: 78,   crit: 90,   unit: "°C",    nominal: "50–80°C" },
  vibration:      { warn: 0.50, crit: 0.70, unit: "mm/s",  nominal: "0.1–0.5 mm/s" },
  pressure:       { warn: 88,   crit: 80,   unit: "PSI",   nominal: "90–110 PSI" },
  oil_temp:       { warn: 65,   crit: 75,   unit: "°C",    nominal: "40–65°C" },
  motor_current:  { warn: 16,   crit: 19,   unit: "A",     nominal: "8–16 A" },
};

function jitter(val: number, pct = 0.015) {
  return val + val * (Math.random() - 0.5) * pct;
}

function getStatus(data: any) {
  if (!data) return "normal";
  if (data.temperature >= 90 || data.vibration >= 0.70 || data.motor_current >= 19) return "emergency";
  if (data.temperature >= 85 || data.vibration >= 0.60 || data.motor_current >= 17) return "critical";
  if (data.temperature >= 78 || data.vibration >= 0.50 || data.oil_temp >= 65) return "warning";
  return "normal";
}


const SENSOR_LABELS: Record<string, string> = {
  temperature:   "Bearing Temperature",
  vibration:     "Vibration Velocity",
  pressure:      "Discharge Pressure",
  oil_temp:      "Oil Temperature",
  motor_current: "Motor Current",
};

const SENSOR_KEYS = ["temperature", "vibration", "pressure", "oil_temp", "motor_current"];

// ─── Plant Overview types & demo data ───────────────────────────
type FleetAsset = {
  equipment_id: string;
  label: string;
  type: string;
  location: string;
  criticality: string;
  health_score: number;
  alert_level: string;
  failure_probability: number;
  predicted_rul_days?: number;
  last_maintenance: string;
};

const ALERT_COLOR: Record<string, string> = {
  EMERGENCY: "text-rose-700 bg-rose-50 border-rose-300",
  CRITICAL:  "text-rose-600 bg-rose-50 border-rose-200",
  WARNING:   "text-amber-600 bg-amber-50 border-amber-200",
  NORMAL:    "text-emerald-600 bg-emerald-50 border-emerald-200",
};

const PRIORITY_ORDER: Record<string, number> = { EMERGENCY: 0, CRITICAL: 1, WARNING: 2, NORMAL: 3 };

// Per-equipment labels and last maintenance dates (realistic: low health = older maintenance)
const EQUIP_LABELS: Record<string, string> = {
  "Pump-B": "BF Cooling Pump", "Pump-A": "BF Cooling Pump", "Pump-C": "BF Cooling Pump",
  "Blast-Furnace": "Blast Furnace", "Conveyor-B": "Raw Material Conveyor",
  "Cooling-Fan-4": "Sinter Cooling Fan", "Rolling-Mill": "Hot Rolling Mill",
  "Cooling-Unit": "Steel Melting Cooler", "Power-Unit": "Power Distribution Unit",
  "Compressor-2": "O₂ Plant Compressor",
};
const MAINT_DATES: Record<string, string> = {
  "Pump-B": "2026-06-05", "Blast-Furnace": "2026-06-04",
  "Conveyor-B": "2026-06-08", "Rolling-Mill": "2026-06-07",
  "Pump-A": "2026-06-12", "Cooling-Fan-4": "2026-06-11",
  "Cooling-Unit": "2026-06-13", "Power-Unit": "2026-06-12",
  "Pump-C": "2026-06-11", "Compressor-2": "2026-06-10",
};

const DEMO_FLEET: FleetAsset[] = [
  { equipment_id: "Pump-B",        label: "BF Cooling Pump",         type: "pump",     location: "Blast Furnace #3",     criticality: "Critical", health_score: 62,  alert_level: "CRITICAL", failure_probability: 0.82, predicted_rul_days: 4.3,   last_maintenance: "2026-06-05" },
  { equipment_id: "Pump-A",        label: "BF Cooling Pump",         type: "pump",     location: "Blast Furnace #2",     criticality: "High",     health_score: 84,  alert_level: "NORMAL",   failure_probability: 0.18, predicted_rul_days: 62.0,  last_maintenance: "2026-06-12" },
  { equipment_id: "Pump-C",        label: "BF Cooling Pump",         type: "pump",     location: "Blast Furnace #4",     criticality: "Critical", health_score: 91,  alert_level: "NORMAL",   failure_probability: 0.06, predicted_rul_days: 120.0, last_maintenance: "2026-06-11" },
  { equipment_id: "Conveyor-B",    label: "Raw Material Conveyor",   type: "conveyor", location: "Raw Material Yard",     criticality: "High",     health_score: 73,  alert_level: "WARNING",  failure_probability: 0.45, predicted_rul_days: 18.2,  last_maintenance: "2026-06-08" },
  { equipment_id: "Cooling-Fan-4", label: "Sinter Cooling Fan",      type: "fan",      location: "Sinter Plant",          criticality: "Medium",   health_score: 88,  alert_level: "NORMAL",   failure_probability: 0.09, predicted_rul_days: 95.0,  last_maintenance: "2026-06-11" },
  { equipment_id: "Rolling-Mill",  label: "Hot Rolling Mill",        type: "mill",     location: "Hot Rolling Section",   criticality: "Critical", health_score: 78,  alert_level: "WARNING",  failure_probability: 0.35, predicted_rul_days: 22.5,  last_maintenance: "2026-06-07" },
  { equipment_id: "Cooling-Unit",  label: "Steel Melting Cooler",    type: "fan",      location: "Steel Melting Shop",    criticality: "Medium",   health_score: 92,  alert_level: "NORMAL",   failure_probability: 0.05, predicted_rul_days: 110.0, last_maintenance: "2026-06-13" },
  { equipment_id: "Power-Unit",    label: "Power Distribution Unit", type: "pump",     location: "Power Distribution",    criticality: "High",     health_score: 97,  alert_level: "NORMAL",   failure_probability: 0.01, predicted_rul_days: 145.0, last_maintenance: "2026-06-12" },
  { equipment_id: "Blast-Furnace", label: "Blast Furnace",           type: "furnace",  location: "Blast Furnace #1",      criticality: "Critical", health_score: 55,  alert_level: "CRITICAL", failure_probability: 0.71, predicted_rul_days: 6.1,   last_maintenance: "2026-06-04" },
  { equipment_id: "Compressor-2",  label: "O₂ Plant Compressor",     type: "pump",     location: "Oxygen Plant",          criticality: "High",     health_score: 86,  alert_level: "NORMAL",   failure_probability: 0.12, predicted_rul_days: 78.0,  last_maintenance: "2026-06-10" },
];

// Next PM Due = today + RUL - 2-day safety buffer (floored at "OVERDUE")
function calcNextPmDue(rul?: number): { label: string; urgent: boolean; soon: boolean } {
  if (rul == null) return { label: "—", urgent: false, soon: false };
  const today = new Date("2026-06-14");
  const daysUntilPm = Math.floor(rul) - 2;
  if (daysUntilPm <= 0) return { label: "OVERDUE", urgent: true, soon: false };
  const due = new Date(today.getTime() + daysUntilPm * 86400000);
  const fmt = due.toISOString().split("T")[0];
  return { label: fmt, urgent: daysUntilPm < 7, soon: daysUntilPm < 30 };
}

// ─── Plant Overview component ────────────────────────────────────
function PlantOverview({ onRunDiagnostics }: { onRunDiagnostics: (eqId: string) => void }) {
  const fleet   = useFleet();
  const loading = fleet.length === 0;

  const fleetHealth = fleet.length ? fleet.reduce((s, e) => s + e.health_score, 0) / fleet.length : 0;
  const critical    = fleet.filter(e => e.alert_level === "CRITICAL" || e.alert_level === "EMERGENCY").length;
  const warning     = fleet.filter(e => e.alert_level === "WARNING").length;

  return (
    <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between" style={{ background: "#ffffff" }}>
        <div>
          <h3 className="font-bold text-2xl" style={{ color: "#1d1d1f" }}>Plant Overview</h3>
        </div>
        <div className="flex items-center gap-8 text-center">
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-medium">Fleet Health</div>
            <div className="text-2xl font-bold mt-0.5 text-slate-900">
              {fleetHealth.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-medium">Critical Assets</div>
            <div className="text-2xl font-bold mt-0.5 text-slate-900">{critical}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-medium">Warnings</div>
            <div className="text-2xl font-bold mt-0.5 text-slate-900">{warning}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide font-medium">Total Monitored</div>
            <div className="text-2xl font-bold mt-0.5 text-slate-900">{fleet.length}</div>
          </div>
        </div>
      </div>

      {/* Asset cards grid */}
      <div className="p-5">
        {loading ? (
          <div className="text-sm text-slate-400 text-center py-6">Loading fleet status…</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {[...fleet].sort((a, b) => (PRIORITY_ORDER[a.alert_level] ?? 4) - (PRIORITY_ORDER[b.alert_level] ?? 4)).map(asset => {
              return (
                <div key={asset.equipment_id}
                  onClick={() => onRunDiagnostics(asset.equipment_id)}
                  className="rounded-2xl bg-white overflow-hidden transition-transform duration-150 hover:scale-[1.02] active:scale-[0.98]"
                  style={{ boxShadow: "0 1px 6px rgba(0,0,0,0.07)", border: "1px solid #e5e7eb", cursor: "pointer" }}>

                  {/* Status bar at top */}
                  <div className={`h-1 w-full ${asset.alert_level === "EMERGENCY" || asset.alert_level === "CRITICAL" ? "bg-rose-500" : asset.alert_level === "WARNING" ? "bg-amber-400" : "bg-emerald-400"}`} />

                  <div className="px-3 pt-2.5 pb-3">
                    {/* Equipment ID + status badge */}
                    <div className="flex items-start justify-between mb-0.5">
                      <span className="font-bold text-slate-900 text-sm leading-tight">{asset.equipment_id}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${
                        asset.alert_level === "EMERGENCY" ? "bg-rose-100 text-rose-700 border-rose-200" :
                        asset.alert_level === "CRITICAL"  ? "bg-rose-50 text-rose-600 border-rose-200" :
                        asset.alert_level === "WARNING"   ? "bg-amber-50 text-amber-600 border-amber-200" :
                        "bg-emerald-50 text-emerald-600 border-emerald-200"}`}>
                        {asset.alert_level}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 mb-3">{asset.location}</div>

                    {/* Health Score — dynamic from Isolation Forest */}
                    <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                      <span>Asset Health</span>
                      <span className={`font-bold text-xs ${asset.alert_level === "EMERGENCY" || asset.alert_level === "CRITICAL" ? "text-rose-600" : asset.alert_level === "WARNING" ? "text-amber-500" : "text-emerald-600"}`}>
                        {asset.health_score.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 mb-3">
                      <div className={`h-1.5 rounded-full transition-all duration-700 ${asset.alert_level === "EMERGENCY" || asset.alert_level === "CRITICAL" ? "bg-rose-500" : asset.alert_level === "WARNING" ? "bg-amber-400" : "bg-emerald-500"}`}
                        style={{ width: `${asset.health_score}%` }} />
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Diagnostics Panel ───────────────────────────────────────────
type DiagData = {
  health_score: number;
  predicted_rul_days: number;
  failure_probability: number;
  alert_level: string;
  predicted_failure_type?: string;
  root_cause?: string;
  diagnosis?: string;
  recommended_actions?: { action: string; priority: string; sop_reference: string }[];
  maintenance_priority?: string;
  sensors?: Record<string, number>;  // snapshot at click time — never changes after
};

const PRIORITY_STYLE: Record<string, string> = {
  P1: "bg-rose-100 text-rose-800",
  P2: "bg-amber-100 text-amber-800",
  P3: "bg-blue-100 text-blue-800",
  Routine: "bg-slate-100 text-slate-600",
};

function smartFailureMode(s: Record<string, number>, predicted?: string): string {
  if (predicted) return predicted.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  const { temperature, vibration, oil_temp, motor_current, pressure } = s;
  if (temperature >= 90 && oil_temp >= 65) return "Bearing / Lubrication Failure";
  if (temperature >= 90) return "Thermal Overload — Bearing Seizure";
  if (vibration >= 0.70) return "Mechanical Failure — Bearing / Shaft Damage";
  if (vibration >= 0.60 && temperature >= 80) return "Bearing Degradation (Thermal-Mechanical)";
  if (motor_current >= 19) return "Electrical Overload — Motor / Shaft Fault";
  if (pressure < 80) return "Hydraulic Failure — Impeller / Cavitation";
  if (oil_temp >= 65) return "Lubrication System Degradation";
  if (temperature >= 78 || vibration >= 0.50) return "Early-Stage Degradation — Trend Monitoring";
  return "No Fault Detected — Normal Operation";
}

function smartRootCause(s: Record<string, number>, fromLogbook?: string): string {
  if (fromLogbook && fromLogbook !== "No significant fault detected") return fromLogbook;
  const { temperature, vibration, oil_temp, motor_current, pressure } = s;
  const faults: string[] = [];
  if (temperature >= 90) faults.push(`critical bearing overheating (${temperature.toFixed(1)}°C vs 50–80°C nominal) — thermal runaway risk`);
  else if (temperature >= 85) faults.push(`bearing temperature approaching critical limit (${temperature.toFixed(1)}°C)`);
  else if (temperature >= 78) faults.push(`mildly elevated bearing temperature (${temperature.toFixed(1)}°C)`);
  if (vibration >= 0.70) faults.push(`severe mechanical imbalance detected (${vibration.toFixed(3)} mm/s, ISO 10816-3 Zone D — immediate action required)`);
  else if (vibration >= 0.60) faults.push(`high vibration indicating bearing wear (${vibration.toFixed(3)} mm/s, Zone C)`);
  else if (vibration >= 0.50) faults.push(`elevated vibration entering warning zone (${vibration.toFixed(3)} mm/s)`);
  if (oil_temp >= 75) faults.push(`oil temperature critically high (${oil_temp.toFixed(1)}°C) — lubrication film failure`);
  else if (oil_temp >= 65) faults.push(`oil temperature elevated (${oil_temp.toFixed(1)}°C) — viscosity degradation risk`);
  if (motor_current >= 19) faults.push(`motor overload (${motor_current.toFixed(1)} A vs 8–16 A nominal) — shaft or bearing resistance`);
  else if (motor_current >= 16) faults.push(`elevated motor current (${motor_current.toFixed(1)} A) — increased mechanical load`);
  if (pressure < 80) faults.push(`critically low discharge pressure (${pressure.toFixed(1)} PSI) — impeller damage or cavitation`);
  else if (pressure < 88) faults.push(`reduced discharge pressure (${pressure.toFixed(1)} PSI) — partial blockage or impeller wear`);
  if (faults.length === 0) return "All sensor parameters within nominal operating envelope. Routine age-related degradation. No corrective action required.";
  let cause = `Primary fault: ${faults[0].charAt(0).toUpperCase() + faults[0].slice(1)}.`;
  if (faults.length > 1) cause += ` Contributing factors: ${faults.slice(1).join("; ")}.`;
  if (temperature >= 85 && vibration >= 0.60) cause += " Combined thermal-mechanical signature is consistent with bearing race failure and lubrication starvation.";
  else if (temperature >= 85 && oil_temp >= 65) cause += " Thermal correlation between bearing and oil sensors indicates a blocked lubrication supply line.";
  else if (vibration >= 0.50 && motor_current >= 16) cause += " Vibration-current correlation indicates shaft misalignment or rotor imbalance.";
  return cause;
}

function smartActions(s: Record<string, number>, fromLogbook?: { action: string; priority: string; sop_reference: string }[]): { action: string; priority: string; sop_reference: string }[] {
  if (fromLogbook && fromLogbook.length > 0 && fromLogbook[0].action !== "Run full AI diagnosis in AI Copilot for specific recommendations") return fromLogbook;
  const { temperature, vibration, oil_temp, motor_current, pressure } = s;
  const acts: { action: string; priority: string; sop_reference: string }[] = [];
  if (temperature >= 90 || vibration >= 0.70) acts.push({ action: "Initiate controlled shutdown — bearing failure risk is imminent; isolate equipment", priority: "P1", sop_reference: "SOP-EMERGENCY-001 §3.1" });
  if (temperature >= 85 || oil_temp >= 65) acts.push({ action: "Inspect and flush lubrication system — verify oil supply filter and line pressure", priority: temperature >= 90 ? "P1" : "P2", sop_reference: "SOP-LUBRICATION-001 §2.1" });
  if (vibration >= 0.60) acts.push({ action: "Perform FFT vibration spectrum analysis to isolate dominant frequency and bearing fault signature", priority: "P1", sop_reference: "SOP-VIBRATION-001 §2.2" });
  else if (vibration >= 0.50) acts.push({ action: "Vibration spectrum analysis and bearing visual inspection within 24 hours", priority: "P2", sop_reference: "SOP-VIBRATION-001 §2" });
  if (temperature >= 78) acts.push({ action: `Replace bearing assembly — SKF 6205 bearing kit ${temperature >= 90 ? "(emergency stock — central store)" : "(schedule within RUL window)"}`, priority: temperature >= 90 ? "P1" : "P2", sop_reference: "SOP-BEARING-001 §4.3" });
  if (motor_current >= 16) acts.push({ action: "Check shaft alignment and coupling condition using dial indicator — correct misalignment if > 0.05 mm", priority: "P2", sop_reference: "SOP-ALIGNMENT-001 §2" });
  if (pressure < 88) acts.push({ action: "Inspect impeller and pump casing for erosion, cavitation pitting, or blockage", priority: "P2", sop_reference: "SOP-PUMP-001 §5.2" });
  if (acts.length === 0) {
    acts.push({ action: "Continue routine monitoring per scheduled maintenance plan — no immediate action required", priority: "Routine", sop_reference: "PM-GUIDE-001 §4" });
    acts.push({ action: "Update CMMS with latest sensor readings; schedule next PM inspection", priority: "Routine", sop_reference: "PM-GUIDE-001 §5" });
  }
  return acts;
}

function DiagnosticsPanel({ eqId, data, sensors }: { eqId: string; data: DiagData | null; sensors?: Record<string, number> }) {
  if (!data) return null;
  const s = sensors || { temperature: 70, vibration: 0.3, pressure: 95, oil_temp: 55, motor_current: 14 };
  const failureMode = smartFailureMode(s, data.predicted_failure_type);
  const rootCause   = smartRootCause(s, data.root_cause || data.diagnosis);
  const actions     = smartActions(s, data.recommended_actions);

  return (
    <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      <div className="px-6 py-4 border-b border-slate-100" style={{ background: "#ffffff" }}>
        <div className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#6e6e73" }}>Diagnostics</div>
        <h3 className="font-bold text-base" style={{ color: "#1d1d1f" }}>{eqId} — Full Asset Diagnostics</h3>
      </div>
      <div className="p-6 space-y-5">
        {/* Health metrics */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Health Score",          val: `${Math.round(data.health_score)}%`,                        color: "#111827" },
            { label: "Remaining Useful Life", val: `${data.predicted_rul_days?.toFixed(1) ?? "—"} days`,   color: "#111827" },
            { label: "Failure Probability",   val: `${Math.round((data.failure_probability ?? 0) * 100)}%`, color: "#111827" },
            { label: "Alert Status",          val: data.alert_level,                                         color: "#111827" },
          ].map(m => (
            <div key={m.label} className="rounded-xl p-4" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
              <div className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: "#6e6e73" }}>{m.label}</div>
              <div className="text-xl font-bold" style={{ color: m.color }}>{m.val}</div>
            </div>
          ))}
        </div>

        {/* Failure mode + root cause */}
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl p-4" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
            <div className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "#6e6e73" }}>Predicted Failure Mode</div>
            <div className="text-sm font-semibold" style={{ color: "#1d1d1f" }}>{failureMode}</div>
          </div>
          <div className="rounded-xl p-4" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
            <div className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: "#6e6e73" }}>Root Cause Analysis</div>
            <div className="text-sm leading-relaxed" style={{ color: "#1d1d1f" }}>{rootCause}</div>
          </div>
        </div>

        {/* Recommended actions */}
        <div className="rounded-xl p-4" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
          <div className="text-[10px] font-bold uppercase tracking-wider mb-3" style={{ color: "#6e6e73" }}>Recommended Maintenance Actions</div>
          <div className="space-y-2">
            {actions.slice(0, 4).map((a, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className={`px-1.5 py-0.5 rounded font-bold shrink-0 ${PRIORITY_STYLE[a.priority] || PRIORITY_STYLE.Routine}`}>{a.priority}</span>
                <span style={{ color: "#1d1d1f" }}>{a.action}</span>
                <span className="ml-auto font-mono shrink-0 text-right" style={{ color: "#c7c7cc" }}>{a.sop_reference}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Splash critical asset definitions ───────────────────────────
const SPLASH_ASSETS = [
  { id: "Blast-Furnace", shortId: "BF-01",  location: "Blast Furnace #1",    alert: "CRITICAL", health: 55, rul: 12, fail: 71, baseTemp: 81.0,  baseVibr: 0.581, baseCurr: 16.8, failMode: "Bearing failure — predicted" },
  { id: "Pump-B",        shortId: "PMP-B",  location: "Blast Furnace #3",    alert: "CRITICAL", health: 62, rul: 9,  fail: 82, baseTemp: 92.5,  baseVibr: 0.720, baseCurr: 18.2, failMode: "Bearing overheating — predicted" },
  { id: "Conveyor-B",   shortId: "CNV-B",  location: "Raw Material Yard",    alert: "WARNING",  health: 73, rul: 18, fail: 45, baseTemp: 74.0,  baseVibr: 0.520, baseCurr: 15.5, failMode: "Belt wear — predicted" },
  { id: "Rolling-Mill", shortId: "RM-01",  location: "Hot Rolling Section",  alert: "WARNING",  health: 78, rul: 22, fail: 35, baseTemp: 69.0,  baseVibr: 0.320, baseCurr: 14.0, failMode: "Roll degradation — predicted" },
];

// ─── Splash Screen ───────────────────────────────────────────────
function SplashScreen({ onEnter, onAskQuestion }: { onEnter: (assetId?: string) => void; onAskQuestion: (q: string) => void }) {
  const [exiting, setExiting]     = useState(false);
  const [tick, setTick]           = useState(0);
  const [clockStr, setClockStr]   = useState("");
  const [assetIdx, setAssetIdx]   = useState(0);
  const [fadeCard, setFadeCard]   = useState(true);
  const [question, setQuestion]   = useState("");

  useEffect(() => {
    setClockStr(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    const cId = setInterval(() => setClockStr(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })), 1000);
    const sId = setInterval(() => setTick(t => t + 1), 2500);
    const aId = setInterval(() => {
      setFadeCard(false);
      setTimeout(() => {
        setAssetIdx(i => (i + 1) % SPLASH_ASSETS.length);
        setFadeCard(true);
      }, 350);
    }, 4000);
    return () => { clearInterval(cId); clearInterval(sId); clearInterval(aId); };
  }, []);

  const asset = SPLASH_ASSETS[assetIdx];
  const isCritical = asset.alert === "CRITICAL";
  const accentColor = isCritical ? "#ef4444" : "#f59e0b";
  const accentBg    = isCritical ? "rgba(239,68,68,0.1)"  : "rgba(245,158,11,0.1)";
  const accentBorder= isCritical ? "rgba(239,68,68,0.25)" : "rgba(245,158,11,0.25)";

  const temp = (asset.baseTemp + Math.sin(tick * 0.8) * 1.5).toFixed(1);
  const vibr = (asset.baseVibr + Math.cos(tick * 1.1) * 0.018).toFixed(3);
  const curr = (asset.baseCurr + Math.sin(tick * 0.6) * 0.4).toFixed(1);

  const go = (target?: string) => { setExiting(true); setTimeout(() => onEnter(target), 700); };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 200,
      background: "#060606",
      opacity: exiting ? 0 : 1,
      transition: "opacity 0.7s cubic-bezier(0.4,0,0.2,1)",
      pointerEvents: exiting ? "none" : "all",
      display: "flex", flexDirection: "column",
    }}>
      {/* Top bar */}
      <div style={{ padding: "22px 48px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #111" }}>
        <span style={{ color: "#e5e7eb", fontSize: 10, fontWeight: 700, letterSpacing: 4, textTransform: "uppercase" as const }}>Autonomous Maintenance Intelligence</span>
        <span style={{ color: "#e5e7eb", fontSize: 11, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase" as const }}>Tata Steel · Hackathon 2026</span>
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", padding: "0 48px", gap: "6vw" }}>
        {/* Hero text */}
        <div style={{ flex: 1, maxWidth: 620 }}>



          <h1 style={{
            color: "#fff",
            fontSize: "clamp(72px, 11vw, 150px)",
            fontWeight: 400,
            lineHeight: 0.9,
            letterSpacing: 4,
            marginTop: 0,
            marginBottom: 14,
            fontFamily: "'Bebas Neue', Impact, sans-serif",
          }}>
            STELOS
          </h1>
          <h2 style={{
            color: "#fff",
            fontSize: "clamp(18px, 2vw, 28px)",
            fontWeight: 700,
            lineHeight: 1.1,
            letterSpacing: -0.5,
            marginBottom: 14,
            fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif",
          }}>
            Know What's Next.<br />Before It Happens.
          </h2>
          <p style={{ color: "#e5e7eb", fontSize: 13, lineHeight: 1.6, maxWidth: 480, marginBottom: 24 }}>
            STELOS transforms machine signals into predictive intelligence, helping teams anticipate failures, optimize maintenance, and protect production before downtime occurs.
          </p>
          {/* Ask a question bar */}
          <form
            onSubmit={e => { e.preventDefault(); if (question.trim()) { setExiting(true); setTimeout(() => onAskQuestion(question.trim()), 700); } }}
            style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 12, border: "1px solid #2a2a2a", borderRadius: 4, overflow: "hidden", background: "#0d0d0d" }}
          >
            <input
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder="Ask anything about your plant health…"
              style={{
                flex: 1, background: "transparent", border: "none", outline: "none",
                color: "#fff", fontSize: 13, padding: "13px 16px",
                fontFamily: "-apple-system, sans-serif",
              }}
            />
            <button type="submit" disabled={!question.trim()} style={{
              background: question.trim() ? "#0071e3" : "#1a1a1a",
              border: "none", color: "#fff", padding: "13px 18px",
              cursor: question.trim() ? "pointer" : "default",
              fontSize: 16, transition: "background 0.2s",
            }}>→</button>
          </form>

          <button
            onClick={() => go()}
            style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              background: "transparent", border: "1px solid #2a2a2a",
              color: "#e5e7eb", fontSize: 12, fontWeight: 600, letterSpacing: 1.2,
              padding: "10px 22px", cursor: "pointer",
              textTransform: "uppercase" as const, transition: "all 0.2s",
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = "#555"; (e.currentTarget as HTMLElement).style.color = "#fff"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = "#2a2a2a"; (e.currentTarget as HTMLElement).style.color = "#e5e7eb"; }}
          >
            Launch Dashboard <span style={{ fontSize: 14 }}>→</span>
          </button>
        </div>

        {/* Critical asset card — cycles through critical/warning assets */}
        <div style={{ width: 300, flexShrink: 0 }}>
          <div
            onClick={() => go(asset.id)}
            style={{
              background: "#0a0a0a", border: "1px solid #1e1e1e", borderTop: `3px solid ${accentColor}`,
              padding: "28px", boxShadow: `0 0 32px ${accentBg}`,
              opacity: fadeCard ? 1 : 0, transition: "opacity 0.35s ease, box-shadow 0.2s ease",
              cursor: "pointer",
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.boxShadow = `0 0 48px ${accentBg}, 0 0 0 1px ${accentColor}`; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.boxShadow = `0 0 32px ${accentBg}`; }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ color: "#e5e7eb", fontSize: 10, letterSpacing: 3, textTransform: "uppercase" as const, fontWeight: 700 }}>{asset.location}</span>
              <span style={{ color: accentColor, fontSize: 11, letterSpacing: 2, fontWeight: 800, display: "flex", alignItems: "center", gap: 5, background: accentBg, padding: "3px 8px", border: `1px solid ${accentBorder}` }}>
                <span className="inline-block w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: accentColor }} />
                {asset.alert}
              </span>
            </div>
            <div style={{ color: "#fff", fontSize: 52, fontWeight: 900, letterSpacing: -2, lineHeight: 1, marginBottom: 4 }}>{asset.shortId}</div>
            <div style={{ color: "#e5e7eb", fontSize: 12, marginBottom: 24 }}>{asset.failMode}</div>
            <div style={{ borderTop: "1px solid #1e1e1e", marginBottom: 20 }} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 20 }}>
              {([
                ["Health", `${asset.health}%`, asset.health < 65 ? "#ef4444" : "#f59e0b"],
                ["RUL",    `${asset.rul}d`,    asset.rul < 14 ? "#f59e0b" : "#10b981"],
                ["Fail.",  `${asset.fail}%`,   asset.fail > 60 ? "#ef4444" : "#f59e0b"],
              ] as const).map(([label, val, color]) => (
                <div key={label}>
                  <div style={{ color: "#444", fontSize: 9, letterSpacing: 3, textTransform: "uppercase" as const, marginBottom: 6, fontWeight: 700 }}>{label}</div>
                  <div style={{ color, fontSize: 26, fontWeight: 900, lineHeight: 1 }}>{val}</div>
                </div>
              ))}
            </div>
            <div style={{ borderTop: "1px solid #1e1e1e", marginBottom: 20 }} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              {[["Temp", `${temp}°C`], ["Vibr", vibr], ["Curr", `${curr}A`]].map(([label, val]) => (
                <div key={label}>
                  <div style={{ color: "#444", fontSize: 9, letterSpacing: 3, textTransform: "uppercase" as const, marginBottom: 6, fontWeight: 700 }}>{label}</div>
                  <div style={{ color: accentColor, fontSize: 14, fontWeight: 700, fontFamily: "monospace" }}>{val}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #1e1e1e", display: "flex", alignItems: "center", gap: 8 }}>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span style={{ color: "#e5e7eb", fontSize: 10, letterSpacing: 1, fontFamily: "monospace" }}>LIVE · {clockStr}</span>
            </div>
          </div>
          <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", padding: "0 2px" }}>
            {["10 ASSETS", "2 CRITICAL", "2 WARNING"].map(label => (
              <span key={label} style={{ color: "#e5e7eb", fontSize: 10, letterSpacing: 2, fontWeight: 600 }}>{label}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: "16px 48px", borderTop: "1px solid #111", display: "flex", justifyContent: "space-between" }}>
        <span style={{ color: "#e5e7eb", fontSize: 11 }}>Jamshedpur Plant · 10 Assets Monitored</span>
        <span style={{ color: "#555", fontSize: 11 }}>LangGraph · XGBoost · Weibull RUL · FAISS RAG · Groq LLM · Gemini Flash</span>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────
function AssetsPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [selectedEq, setSelectedEq] = useState(EQUIPMENT_LIST[0]);
  const [latest, setLatest]         = useState<any>(EQUIPMENT_LIST[0].base);
  const [diagData, setDiagData]         = useState<DiagData | null>(null);
  const [diagLoading, setDiagLoading]   = useState(false);
  const twinRef = useRef<HTMLDivElement>(null);

  const [entered, setEntered]           = useState(false);
  const [splashReady, setSplashReady]   = useState(false);

  useEffect(() => {
    const wasEntered = sessionStorage.getItem("sg_ctrl") === "1";
    if (wasEntered) {
      setEntered(true);
      if (!window.history.state?.dashboard) {
        window.history.replaceState({ dashboard: true }, "");
      }
    } else {
      window.history.replaceState({ splash: true }, "");
    }
    setSplashReady(true);
  }, []);

  useEffect(() => {
    const handlePop = (e: PopStateEvent) => {
      if (e.state?.splash || !e.state) {
        sessionStorage.removeItem("sg_ctrl");
        setEntered(false);
      }
    };
    window.addEventListener("popstate", handlePop);
    return () => window.removeEventListener("popstate", handlePop);
  }, []);

  const handleEnter = (target?: string) => {
    sessionStorage.setItem("sg_ctrl", "1");
    window.history.pushState({ dashboard: true }, "");
    setEntered(true);
    if (target === "console") {
      router.push("/console");
    } else if (target) {
      const eq = EQUIPMENT_LIST.find(e => e.id === target) || EQUIPMENT_LIST[0];
      setSelectedEq(eq);
      fetchDiagnostics(target);
      setTimeout(() => twinRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 800);
    }
  };

  // Live sensor readings for KPI cards
  useEffect(() => {
    setLatest(selectedEq.base);
    let ws: WebSocket | null = null;
    let simInterval: ReturnType<typeof setInterval> | null = null;
    let wsConnected = false;
    try {
      const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000") + "/ws/sensors";
      ws = new WebSocket(wsUrl);
      ws.onopen = () => { wsConnected = true; };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLatest({
          temperature:   data.temperature   ?? selectedEq.base.temperature,
          vibration:     data.vibration     ?? selectedEq.base.vibration,
          pressure:      data.pressure      ?? selectedEq.base.pressure,
          oil_temp:      data.oil_temp      ?? selectedEq.base.oil_temp,
          motor_current: data.motor_current ?? selectedEq.base.motor_current,
        });
      };
      ws.onerror = () => { wsConnected = false; };
    } catch { wsConnected = false; }
    simInterval = setInterval(() => {
      if (!wsConnected) {
        const b = selectedEq.base;
        setLatest({
          temperature:   parseFloat(jitter(b.temperature).toFixed(1)),
          vibration:     parseFloat(jitter(b.vibration).toFixed(3)),
          pressure:      parseFloat(jitter(b.pressure).toFixed(1)),
          oil_temp:      parseFloat(jitter(b.oil_temp).toFixed(1)),
          motor_current: parseFloat(jitter(b.motor_current).toFixed(1)),
        });
      }
    }, 2000);
    return () => { ws?.close(); if (simInterval) clearInterval(simInterval); };
  }, [selectedEq]);

  // Fetch full diagnostics — always shows something, enriches with live data when available
  const fetchDiagnostics = async (eqId: string) => {
    setDiagLoading(true);

    // Start with static base so panel always renders
    const eqBase = EQUIPMENT_LIST.find(e => e.id === eqId);
    const b = eqBase?.base;
    const baseAlert = b
      ? (b.temperature >= 90 || b.vibration >= 0.70 ? "EMERGENCY"
        : b.temperature >= 85 || b.vibration >= 0.60 ? "CRITICAL"
        : b.temperature >= 78 || b.vibration >= 0.50 ? "WARNING" : "NORMAL")
      : "NORMAL";

    // Snapshot sensors from stable base values (NOT live jitter) — locked at click time
    const sensorSnapshot: Record<string, number> = b
      ? { temperature: b.temperature, vibration: b.vibration, pressure: b.pressure, oil_temp: b.oil_temp, motor_current: b.motor_current }
      : { temperature: 70, vibration: 0.3, pressure: 95, oil_temp: 55, motor_current: 14 };

    let healthData: DiagData = {
      health_score:        100 - (b ? (b.temperature - 50) * 0.8 + b.vibration * 30 : 20),
      predicted_rul_days:  b ? Math.max(1, 120 - (b.temperature - 50) * 2) : 30,
      failure_probability: b ? Math.min(0.99, (b.temperature - 50) / 80 + b.vibration * 0.5) : 0.2,
      alert_level:         baseAlert,
      sensors:             sensorSnapshot,
    };

    try {
      // Try live health data (8s timeout for this call)
      const healthRes = await apiFetch("/api/equipment/health", 8000);
      if (healthRes.ok) {
        const hd = await healthRes.json();
        const eq = (hd.equipment || []).find((e: any) => e.equipment_id === eqId);
        if (eq) healthData = {
          ...healthData,
          health_score:           eq.health_score,
          predicted_rul_days:     eq.predicted_rul_days,
          failure_probability:    eq.failure_probability,
          alert_level:            eq.alert_level,
          predicted_failure_type: eq.predicted_failure_type,
          // keep sensor snapshot unchanged — backend gives ML scores, not raw sensor readings
        };
      }
    } catch { /* use base data */ }

    // Show panel immediately with what we have
    setDiagData({ ...healthData });
    setDiagLoading(false);

    // Then try to enrich with logbook (root cause + actions) in background
    try {
      const logRes = await apiFetch(`/api/logbook?equipment_id=${eqId}`, 6000);
      if (logRes.ok) {
        const ld = await logRes.json();
        const entry = (ld.entries || [])[0];
        if (entry) {
          setDiagData(prev => prev ? {
            ...prev,
            root_cause:           entry.root_cause,
            diagnosis:            entry.diagnosis,
            recommended_actions:  entry.recommended_actions,
            maintenance_priority: entry.maintenance_priority,
          } : prev);
        }
      }
    } catch { /* logbook unavailable — panel already showing */ }
  };

  // Auto-select equipment when TopNav asset nav item is clicked (?eq= param)
  useEffect(() => {
    const eqParam = searchParams.get("eq");
    if (!eqParam) return;
    const eq = EQUIPMENT_LIST.find(e => e.id === eqParam);
    if (eq) {
      setSelectedEq(eq);
      fetchDiagnostics(eqParam);
      setTimeout(() => twinRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
    }
  }, [searchParams]);

  // Called when "Run Diagnostics" is clicked on any asset card
  const handleRunDiagnostics = (eqId: string) => {
    const eq = EQUIPMENT_LIST.find(e => e.id === eqId) || EQUIPMENT_LIST[0];
    setSelectedEq(eq);
    fetchDiagnostics(eqId);
    setTimeout(() => twinRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  };

  const status = getStatus(latest);

  const STATUS_BG: Record<string, string> = {
    emergency: "bg-rose-600 text-white shadow-lg shadow-rose-200",
    critical:  "bg-rose-500 text-white shadow-lg shadow-rose-100",
    warning:   "bg-amber-500 text-white shadow-lg shadow-amber-100",
    normal:    "bg-emerald-500 text-white shadow-lg shadow-emerald-100",
  };

  return (
    <>
      {!splashReady && <div style={{ position: "fixed", inset: 0, background: "#060606", zIndex: 200 }} />}
      {splashReady && !entered && <SplashScreen onEnter={handleEnter} onAskQuestion={(q) => { sessionStorage.setItem("sg_ctrl", "1"); window.history.pushState({ dashboard: true }, ""); setEntered(true); router.push(`/console?q=${encodeURIComponent(q)}`); }} />}
      <div className="space-y-5" style={{ padding: "28px 36px", background: "#f8fafc" }}>
        {/* ── Plant Overview (top) ── */}
        <PlantOverview onRunDiagnostics={handleRunDiagnostics} />

      {/* ── Digital Twin section ── */}
      <div ref={twinRef} className="space-y-5 scroll-mt-4">
        {/* Header */}
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight" style={{ color: "#1d1d1f" }}>
              {selectedEq.label.split("—")[0].trim()}
            </h2>
            <p className="text-sm mt-0.5" style={{ color: "#6e6e73" }}>{selectedEq.label.split("—")[1]?.trim()}</p>
          </div>
        </div>

        {/* 5 sensor KPI cards (unchanged) */}
        <div className="grid grid-cols-5 gap-4">
          {SENSOR_KEYS.map(key => {
            const val = latest?.[key] ?? 0;
            const th  = THRESHOLDS[key];
            const isHigh = key === "pressure" ? val < th.crit : val >= th.crit;
            const isWarn = key === "pressure" ? val < th.warn : val >= th.warn;
            const color  = "text-slate-900";
            const dot    = isHigh ? "bg-rose-400"  : isWarn ? "bg-amber-400"  : "bg-emerald-400";
            return (
              <div key={key} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
                <h3 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-4">{SENSOR_LABELS[key]}</h3>
                <div className={`text-3xl font-bold tracking-tight ${color}`}>
                  {key === "vibration" ? val.toFixed(3) : val.toFixed(1)}
                  <span className="text-base font-normal ml-0.5 text-slate-400">{th.unit}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-1.5 font-mono">{th.nominal}</div>
              </div>
            );
          })}
        </div>

        {/* Diagnostics panel (shown after Run Diagnostics or dropdown selection) */}
        {diagLoading && (
          <div className="bg-white rounded-2xl p-8 text-center text-sm" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)", color: "#6e6e73" }}>
            <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" style={{ color: "#0071e3" }} />
            Loading diagnostics for {selectedEq.id}…
          </div>
        )}
        {!diagLoading && diagData && <DiagnosticsPanel eqId={selectedEq.id} data={diagData} sensors={diagData.sensors} />}

      </div>
      </div>
    </>
  );
}

export default function AssetsPage() {
  return (
    <Suspense fallback={null}>
      <AssetsPageInner />
    </Suspense>
  );
}
