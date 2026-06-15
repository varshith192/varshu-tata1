import { useState, useEffect } from "react";
import { apiFetch } from "./api";

export type FleetAsset = {
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
  maintenance_priority?: string;
};

export const BASE_FLEET: FleetAsset[] = [
  { equipment_id: "Pump-B",        label: "BF Cooling Pump",         type: "pump",     location: "Blast Furnace #3",    criticality: "Critical", health_score: 62,  alert_level: "CRITICAL", failure_probability: 0.82, predicted_rul_days: 4.3,   last_maintenance: "2026-06-05", maintenance_priority: "P1" },
  { equipment_id: "Blast-Furnace", label: "Blast Furnace",           type: "furnace",  location: "Blast Furnace #1",    criticality: "Critical", health_score: 55,  alert_level: "CRITICAL", failure_probability: 0.71, predicted_rul_days: 6.1,   last_maintenance: "2026-06-04", maintenance_priority: "P1" },
  { equipment_id: "Conveyor-B",    label: "Raw Material Conveyor",   type: "conveyor", location: "Raw Material Yard",    criticality: "High",     health_score: 73,  alert_level: "WARNING",  failure_probability: 0.45, predicted_rul_days: 18.2,  last_maintenance: "2026-06-08", maintenance_priority: "P2" },
  { equipment_id: "Rolling-Mill",  label: "Hot Rolling Mill",        type: "mill",     location: "Hot Rolling Section",  criticality: "Critical", health_score: 78,  alert_level: "WARNING",  failure_probability: 0.35, predicted_rul_days: 22.5,  last_maintenance: "2026-06-07", maintenance_priority: "P2" },
  { equipment_id: "Pump-A",        label: "BF Cooling Pump",         type: "pump",     location: "Blast Furnace #2",    criticality: "High",     health_score: 84,  alert_level: "NORMAL",   failure_probability: 0.18, predicted_rul_days: 62.0,  last_maintenance: "2026-06-12", maintenance_priority: "P3" },
  { equipment_id: "Compressor-2",  label: "O₂ Plant Compressor",     type: "pump",     location: "Oxygen Plant",         criticality: "High",     health_score: 86,  alert_level: "NORMAL",   failure_probability: 0.12, predicted_rul_days: 78.0,  last_maintenance: "2026-06-10", maintenance_priority: "P3" },
  { equipment_id: "Cooling-Fan-4", label: "Sinter Cooling Fan",      type: "fan",      location: "Sinter Plant",         criticality: "Medium",   health_score: 88,  alert_level: "NORMAL",   failure_probability: 0.09, predicted_rul_days: 95.0,  last_maintenance: "2026-06-11", maintenance_priority: "Routine" },
  { equipment_id: "Cooling-Unit",  label: "Steel Melting Cooler",    type: "fan",      location: "Steel Melting Shop",   criticality: "Medium",   health_score: 92,  alert_level: "NORMAL",   failure_probability: 0.05, predicted_rul_days: 110.0, last_maintenance: "2026-06-13", maintenance_priority: "Routine" },
  { equipment_id: "Pump-C",        label: "BF Cooling Pump",         type: "pump",     location: "Blast Furnace #4",    criticality: "Critical", health_score: 91,  alert_level: "NORMAL",   failure_probability: 0.06, predicted_rul_days: 120.0, last_maintenance: "2026-06-11", maintenance_priority: "Routine" },
  { equipment_id: "Power-Unit",    label: "Power Distribution Unit", type: "pump",     location: "Power Distribution",   criticality: "High",     health_score: 97,  alert_level: "NORMAL",   failure_probability: 0.01, predicted_rul_days: 145.0, last_maintenance: "2026-06-12", maintenance_priority: "Routine" },
];

// Per-equipment drift state (module-level, not reset on re-render)
const _driftVel:  Record<string, number> = {};
const _driftFlip: Record<string, number> = {};

function _alertFromHealth(h: number): string {
  if (h < 50) return "EMERGENCY";
  if (h < 65) return "CRITICAL";
  if (h < 78) return "WARNING";
  return "NORMAL";
}

// ── Singleton store ──────────────────────────────────────────────────────────
let _fleet: FleetAsset[]            = BASE_FLEET.map(e => ({ ...e }));
let _listeners                       = new Set<() => void>();
let _jitterTimer: ReturnType<typeof setInterval> | null = null;
let _fetchTimer:  ReturnType<typeof setInterval> | null = null;
let _initialized                     = false;

function _notify() { _listeners.forEach(fn => fn()); }

function _applyJitter() {
  _fleet = _fleet.map(e => {
    const base = BASE_FLEET.find(b => b.equipment_id === e.equipment_id)!;

    // Flip drift direction every 8–20 ticks (24–60 s)
    _driftFlip[e.equipment_id] = (_driftFlip[e.equipment_id] ?? 1) - 1;
    if (_driftFlip[e.equipment_id] <= 0) {
      _driftVel[e.equipment_id]  = (Math.random() - 0.5) * 3.0;
      _driftFlip[e.equipment_id] = Math.floor(Math.random() * 12) + 8;
    }

    const vel   = _driftVel[e.equipment_id] ?? (Math.random() - 0.5) * 2;
    const noise = (Math.random() - 0.5) * 0.6;

    // Soft mean-reversion: if health drifts >18 pts from base, pull gently back
    const diff = e.health_score - base.health_score;
    const pull = Math.abs(diff) > 18 ? -diff * 0.08 : 0;

    const health  = Math.max(2, Math.min(99, e.health_score + vel + noise + pull));
    const alert   = _alertFromHealth(health);
    const fp      = Math.min(0.99, Math.max(0.01, (100 - health) / 100 + (Math.random() - 0.5) * 0.07));
    const baseRul = base.predicted_rul_days ?? 30;
    const rul     = Math.max(0.5, (health / (base.health_score || 1)) * baseRul + (Math.random() - 0.5) * 2);

    return { ...e, health_score: health, alert_level: alert, failure_probability: fp, predicted_rul_days: rul };
  });
  _notify();
}

async function _fetchFromApi() {
  try {
    const res = await apiFetch("/api/equipment/health");
    if (!res.ok) throw new Error();
    const data = await res.json();
    if (data.equipment?.length) {
      _fleet = data.equipment.map((e: FleetAsset) => ({
        ...BASE_FLEET.find(b => b.equipment_id === e.equipment_id) ?? e,
        health_score:        e.health_score,
        alert_level:         e.alert_level,
        failure_probability: e.failure_probability,
        predicted_rul_days:  e.predicted_rul_days,
      }));
      _notify();
    }
  } catch {
    // keep current fleet data, jitter continues
  }
}

function _init() {
  if (_initialized) return;
  _initialized = true;
  BASE_FLEET.forEach(e => {
    _driftVel[e.equipment_id]  = (Math.random() - 0.5) * 2;
    _driftFlip[e.equipment_id] = Math.floor(Math.random() * 12) + 8;
  });
  _fetchFromApi();
  _jitterTimer = setInterval(_applyJitter, 3000);
  _fetchTimer  = setInterval(_fetchFromApi, 30000);
}

export function getFleet(): FleetAsset[] { return _fleet; }

export function useFleet(): FleetAsset[] {
  const [fleet, setFleet] = useState<FleetAsset[]>(_fleet);
  useEffect(() => {
    _init();
    const update = () => setFleet([..._fleet]);
    _listeners.add(update);
    update();
    return () => { _listeners.delete(update); };
  }, []);
  return fleet;
}
