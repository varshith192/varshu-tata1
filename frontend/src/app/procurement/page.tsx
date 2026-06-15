"use client";

import { useState, useRef, useMemo } from "react";
import { Package, AlertTriangle, Clock, ShoppingCart, TrendingUp, CheckCircle2 } from "lucide-react";
import { useFleet } from "@/lib/fleetStore";

type AvailStatus = "In Stock" | "Low Stock" | "Out of Stock";
type POStatus    = "Pending" | "Approved" | "Shipped" | "Received";

interface Part {
  id: string;
  name: string;
  equipment: string[];
  stock: number;
  unit: string;
  minStock: number;
  orderQty: number;
  status: AvailStatus;
  lead: string;
  source: string;
  costINR: number;
  urgency: "CRITICAL" | "REORDER" | "OK";
}

interface PurchaseOrder {
  id: string;
  partName: string;
  partId: string;
  qty: number;
  lead: string;
  costINR: number;
  status: POStatus;
  equipment: string;
  createdAt?: string;
}

const PARTS: Part[] = [
  { id: "SP-001", name: "Bearing Kit (SKF 6205)",         equipment: ["Pump-B","Blast-Furnace"], stock: 4,  unit: "sets",  minStock: 3,  orderQty: 3,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 45000,  urgency: "OK"       },
  { id: "SP-002", name: "Mechanical Seal (Type-II)",       equipment: ["Pump-B","Pump-A"],        stock: 1,  unit: "set",   minStock: 2,  orderQty: 2,  status: "Low Stock",    lead: "3–5 days",   source: "SAIL Stores",            costINR: 28000,  urgency: "REORDER"  },
  { id: "SP-003", name: "Impeller (316 SS)",               equipment: ["Pump-B","Pump-C"],        stock: 0,  unit: "pcs",   minStock: 2,  orderQty: 2,  status: "Out of Stock", lead: "14–21 days", source: "OEM — Kirloskar",         costINR: 120000, urgency: "CRITICAL" },
  { id: "SP-004", name: "Coupling Insert (Poly)",          equipment: ["Pump-A","Conveyor-B"],    stock: 6,  unit: "pcs",   minStock: 4,  orderQty: 4,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 8000,   urgency: "OK"       },
  { id: "SP-005", name: "V-Belt Set (B-Section)",          equipment: ["Cooling-Fan-4"],          stock: 12, unit: "pcs",   minStock: 8,  orderQty: 8,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 12000,  urgency: "OK"       },
  { id: "SP-006", name: "Fan Blade Assembly",              equipment: ["Cooling-Fan-4"],          stock: 1,  unit: "set",   minStock: 2,  orderQty: 1,  status: "Low Stock",    lead: "7–10 days",  source: "OEM — Howden",           costINR: 320000, urgency: "REORDER"  },
  { id: "SP-007", name: "Conveyor Belt Section (5m)",      equipment: ["Conveyor-B"],             stock: 2,  unit: "rolls", minStock: 2,  orderQty: 2,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 95000,  urgency: "OK"       },
  { id: "SP-008", name: "Drive Chain (80H)",               equipment: ["Conveyor-B"],             stock: 0,  unit: "pcs",   minStock: 1,  orderQty: 2,  status: "Out of Stock", lead: "10–14 days", source: "OEM — Rexnord",          costINR: 42000,  urgency: "CRITICAL" },
  { id: "SP-009", name: "Tuyere Assembly (Complete)",      equipment: ["Blast-Furnace"],          stock: 2,  unit: "sets",  minStock: 2,  orderQty: 1,  status: "In Stock",     lead: "Warehouse",  source: "BF Spares Store",        costINR: 450000, urgency: "OK"       },
  { id: "SP-010", name: "Thermocouple (Type-K)",           equipment: ["Blast-Furnace"],          stock: 12, unit: "pcs",   minStock: 6,  orderQty: 6,  status: "In Stock",     lead: "Warehouse",  source: "Instrumentation Store",  costINR: 8500,   urgency: "OK"       },
  { id: "SP-011", name: "Work Roll (Forged Steel)",        equipment: ["Rolling-Mill"],           stock: 0,  unit: "pcs",   minStock: 1,  orderQty: 1,  status: "Out of Stock", lead: "14–21 days", source: "OEM — Bhilai Roll Plant", costINR: 850000, urgency: "CRITICAL" },
  { id: "SP-012", name: "Hydraulic Cylinder Seal Kit",     equipment: ["Rolling-Mill"],           stock: 3,  unit: "sets",  minStock: 2,  orderQty: 2,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 38000,  urgency: "OK"       },
  { id: "SP-013", name: "Motor Bearing (FAG 6308)",        equipment: ["Cooling-Unit","Pump-A"],  stock: 8,  unit: "pcs",   minStock: 6,  orderQty: 6,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 22000,  urgency: "OK"       },
  { id: "SP-014", name: "Lubrication Oil VG68 (20L)",      equipment: ["All"],                    stock: 4,  unit: "cans",  minStock: 3,  orderQty: 5,  status: "In Stock",     lead: "Warehouse",  source: "Central Store",          costINR: 64000,  urgency: "OK"       },
  { id: "SP-015", name: "Gearbox Oil Seal Kit",            equipment: ["Rolling-Mill"],           stock: 1,  unit: "set",   minStock: 2,  orderQty: 2,  status: "Low Stock",    lead: "5 days",     source: "SAIL Stores",            costINR: 65000,  urgency: "REORDER"  },
];

const PO_SEED: PurchaseOrder[] = [
  { id: "PO-2026-004", partName: "Gearbox Oil Seal Kit",   partId: "SP-015", qty: 2, lead: "5d lead",    costINR: 130000, status: "Pending",  equipment: "Rolling-Mill", createdAt: "2026-06-15T06:00:00" },
  { id: "PO-2026-003", partName: "Cylindrical Roller Brg", partId: "SP-013", qty: 4, lead: "10d lead",   costINR: 88000,  status: "Approved", equipment: "Cooling-Unit", createdAt: "2026-06-14T14:00:00" },
  { id: "PO-2026-002", partName: "Impeller (316 SS)",       partId: "SP-003", qty: 3, lead: "21d lead",   costINR: 360000, status: "Shipped",  equipment: "Pump-B",       createdAt: "2026-06-13T09:00:00" },
  { id: "PO-2026-001", partName: "Drive Chain (80H)",       partId: "SP-008", qty: 2, lead: "In transit", costINR: 84000,  status: "Received", equipment: "Conveyor-B",   createdAt: "2026-06-10T11:00:00" },
];

const PO_STEPS: POStatus[] = ["Pending", "Approved", "Shipped", "Received"];

const AVAIL_STYLE: Record<AvailStatus, { bg: string; text: string }> = {
  "In Stock":     { bg: "#f0fdf4", text: "#065f46" },
  "Low Stock":    { bg: "#fffbeb", text: "#b45309" },
  "Out of Stock": { bg: "#fef2f2", text: "#dc2626" },
};

const URGENCY_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: "#fef2f2", text: "#dc2626", border: "#fecaca" },
  REORDER:  { bg: "#fffbeb", text: "#b45309", border: "#fde68a" },
  OK:       { bg: "#f0fdf4", text: "#065f46", border: "#bbf7d0" },
};

const PO_STATUS_COLOR: Record<POStatus, string> = {
  Pending:  "#f59e0b",
  Approved: "#2563eb",
  Shipped:  "#7c3aed",
  Received: "#10b981",
};

function POTracker({ status }: { status: POStatus }) {
  const idx = PO_STEPS.indexOf(status);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, width: "100%" }}>
      {PO_STEPS.map((step, i) => {
        const done    = i < idx;
        const current = i === idx;
        return (
          <div key={step} style={{ display: "flex", alignItems: "center", flex: 1 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
              <div style={{
                width: 20, height: 20, borderRadius: "50%",
                background: done ? "#10b981" : current ? "#2563eb" : "#e5e7eb",
                border: `2px solid ${done ? "#10b981" : current ? "#2563eb" : "#d1d5db"}`,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {done    && <span style={{ fontSize: 10, color: "#fff", fontWeight: 800 }}>✓</span>}
                {current && <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#fff", display: "block" }} />}
              </div>
              <span style={{ fontSize: 8, fontWeight: current ? 700 : 400, color: done ? "#10b981" : current ? "#2563eb" : "#9ca3af", whiteSpace: "nowrap" }}>{step}</span>
            </div>
            {i < PO_STEPS.length - 1 && (
              <div style={{ flex: 1, height: 2, background: done ? "#10b981" : "#e5e7eb", margin: "0 2px", marginBottom: 14 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function fmtINR(v: number) {
  if (v >= 100000) return `₹${(v / 100000).toFixed(2)}L`;
  return `₹${(v / 1000).toFixed(0)}K`;
}

export default function ProcurementPage() {
  const fleet = useFleet();
  const [filter, setFilter]   = useState<"ALL" | "CRITICAL" | "REORDER">("ALL");
  const [orders, setOrders]   = useState<PurchaseOrder[]>(PO_SEED);
  const poCounterRef          = useRef(PO_SEED.length + 1);

  // Parts that already have an active (non-Received) PO
  const orderedPartIds = useMemo(
    () => new Set(orders.filter(o => o.status !== "Received").map(o => o.partId)),
    [orders]
  );

  function placeOrder(part: Part) {
    const num = String(poCounterRef.current++).padStart(3, "0");
    const id  = `PO-2026-0${num}`;
    setOrders(prev => [{
      id,
      partName:  part.name,
      partId:    part.id,
      qty:       part.orderQty,
      lead:      part.lead,
      costINR:   part.costINR * part.orderQty,
      status:    "Pending" as POStatus,
      equipment: part.equipment[0],
      createdAt: new Date().toISOString(),
    }, ...prev]);
  }

  function advancePO(poId: string) {
    const next: Record<POStatus, POStatus> = {
      Pending:  "Approved",
      Approved: "Shipped",
      Shipped:  "Received",
      Received: "Received",
    };
    setOrders(prev => prev.map(po => po.id === poId ? { ...po, status: next[po.status] } : po));
  }

  function orderAllCritical() {
    PARTS.filter(p => p.urgency === "CRITICAL" && !orderedPartIds.has(p.id)).forEach(placeOrder);
  }

  function clearReceived() {
    setOrders(prev => prev.filter(o => o.status !== "Received"));
  }

  const reorderParts  = PARTS.filter(p => p.urgency !== "OK");
  const criticalParts = PARTS.filter(p => p.urgency === "CRITICAL");
  const openPOs       = orders.filter(p => p.status !== "Received");
  const totalSpend    = orders.reduce((s, p) => s + p.costINR, 0);
  const openSpend     = openPOs.reduce((s, p) => s + p.costINR, 0);
  const filtered      = filter === "ALL" ? reorderParts : PARTS.filter(p => p.urgency === filter);

  return (
    <div style={{ padding: "24px 32px", background: "#f8fafc", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 800, color: "#111827", margin: 0 }}>Procurement Control</h2>
          <p style={{ fontSize: 13, color: "#6b7280", marginTop: 3 }}>Spare parts replenishment, ordering, and purchase order tracking</p>
        </div>
        <button onClick={orderAllCritical}
          style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 18px", borderRadius: 8, background: "#ef4444", color: "#fff", border: "none", cursor: "pointer", fontWeight: 700, fontSize: 13 }}>
          <ShoppingCart size={15} /> Order All Critical
        </button>
      </div>

      {/* ── KPI Strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 18 }}>
        {[
          { label: "Parts Below Reorder",  value: reorderParts.length,       sub: "Need replenishment",          color: "#f59e0b", icon: <Package size={18} color="#f59e0b" /> },
          { label: "Critical Shortages",   value: criticalParts.length,      sub: "At/near zero stock",          color: "#ef4444", icon: <AlertTriangle size={18} color="#ef4444" /> },
          { label: "Open Orders",          value: openPOs.length,            sub: `${fleet.length} assets monitored`, color: "#6366f1", icon: <Clock size={18} color="#6366f1" /> },
          { label: "On-Order Spend",       value: fmtINR(openSpend),         sub: "Committed, not yet received", color: "#10b981", icon: <TrendingUp size={18} color="#10b981" /> },
        ].map((k, i) => (
          <div key={i} style={{ background: "#fff", borderRadius: 14, padding: "16px 20px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)", display: "flex", gap: 14, alignItems: "center" }}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: `${k.color}15`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              {k.icon}
            </div>
            <div>
              <div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af" }}>{k.label}</div>
              <div style={{ fontSize: 26, fontWeight: 900, color: k.color, lineHeight: 1.1 }}>{k.value}</div>
              <div style={{ fontSize: 11, color: "#6b7280" }}>{k.sub}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 420px", gap: 16 }}>

        {/* ── Reorder Recommendations ── */}
        <div style={{ background: "#fff", borderRadius: 14, boxShadow: "0 2px 10px rgba(0,0,0,0.06)", overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #f1f5f9", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#111827" }}>Reorder Recommendations</span>
              <span style={{ marginLeft: 8, fontSize: 11, color: "#ef4444", fontWeight: 600 }}>{reorderParts.length} below reorder</span>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              {(["ALL", "CRITICAL", "REORDER"] as const).map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  style={{ padding: "4px 12px", borderRadius: 20, fontSize: 11, fontWeight: 700, cursor: "pointer", border: "1px solid",
                    borderColor: filter === f ? "#2563eb" : "#e5e7eb",
                    background: filter === f ? "#eff6ff" : "#fff",
                    color: filter === f ? "#2563eb" : "#6b7280" }}>
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  {["Part ID", "Name", "Stock", "Order Qty", "Lead Time", "Urgency", ""].map(h => (
                    <th key={h} style={{ padding: "10px 14px", textAlign: "left", fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1.5, color: "#9ca3af", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(filtered.length > 0 ? filtered : PARTS).map((p, i) => {
                  const us        = URGENCY_STYLE[p.urgency];
                  const isOrdered = orderedPartIds.has(p.id);
                  return (
                    <tr key={p.id} style={{ borderTop: "1px solid #f1f5f9", background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                      <td style={{ padding: "10px 14px", fontSize: 11, fontWeight: 700, color: "#2563eb" }}>{p.id}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "#111827" }}>{p.name}</div>
                        <div style={{ fontSize: 10, color: "#9ca3af" }}>{p.equipment.join(", ")}</div>
                      </td>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: p.stock === 0 ? "#ef4444" : p.stock <= p.minStock ? "#f59e0b" : "#10b981" }}>
                          {p.stock} {p.unit}
                        </span>
                        <div style={{ fontSize: 9, color: "#9ca3af" }}>min {p.minStock}</div>
                      </td>
                      <td style={{ padding: "10px 14px", fontSize: 12, fontWeight: 700, color: "#374151" }}>+{p.orderQty}</td>
                      <td style={{ padding: "10px 14px", fontSize: 11, color: "#6b7280" }}>{p.lead}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 20, background: us.bg, color: us.text, border: `1px solid ${us.border}` }}>
                          {p.urgency}
                        </span>
                      </td>
                      <td style={{ padding: "10px 14px" }}>
                        {p.urgency === "OK" ? (
                          <span style={{ fontSize: 11, color: "#10b981", fontWeight: 600 }}>✓ OK</span>
                        ) : isOrdered ? (
                          <span style={{ fontSize: 11, fontWeight: 700, padding: "4px 12px", borderRadius: 6, background: "#f0fdf4", color: "#065f46", border: "1px solid #bbf7d0", display: "inline-flex", alignItems: "center", gap: 4 }}>
                            <CheckCircle2 size={11} /> Ordered
                          </span>
                        ) : (
                          <button onClick={() => placeOrder(p)}
                            style={{ fontSize: 11, fontWeight: 700, padding: "4px 12px", borderRadius: 6,
                              background: p.urgency === "CRITICAL" ? "#fef2f2" : "#eff6ff",
                              color: p.urgency === "CRITICAL" ? "#dc2626" : "#2563eb",
                              border: `1px solid ${p.urgency === "CRITICAL" ? "#fecaca" : "#bfdbfe"}`,
                              cursor: "pointer" }}>
                            Order
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Purchase Orders ── */}
        <div style={{ background: "#fff", borderRadius: 14, boxShadow: "0 2px 10px rgba(0,0,0,0.06)", overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #f1f5f9", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#111827" }}>Purchase Orders</span>
              <span style={{ marginLeft: 8, fontSize: 11, color: "#6366f1", fontWeight: 700 }}>{openPOs.length} open</span>
            </div>
            <button onClick={clearReceived}
              style={{ fontSize: 11, color: "#9ca3af", background: "none", border: "none", cursor: "pointer" }}>
              Clear received ↺
            </button>
          </div>

          <div style={{ padding: "12px 16px", flex: 1, display: "flex", flexDirection: "column", gap: 12, overflowY: "auto", maxHeight: 540 }}>
            {orders.length === 0 && (
              <div style={{ padding: "40px 0", textAlign: "center", color: "#9ca3af", fontSize: 13 }}>No orders yet</div>
            )}
            {orders.map(po => (
              <div key={po.id} style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: "12px 14px", borderLeft: `3px solid ${PO_STATUS_COLOR[po.status]}` }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 6 }}>
                  <div>
                    <span style={{ fontSize: 11, fontWeight: 700, color: "#2563eb" }}>{po.id}</span>
                    {po.createdAt && (
                      <span style={{ marginLeft: 8, fontSize: 9, color: "#9ca3af" }}>{po.createdAt.slice(0,16).replace("T"," ")}</span>
                    )}
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#111827", marginTop: 2 }}>{po.partName}</div>
                  </div>
                  <span style={{ fontSize: 13, fontWeight: 800, color: "#111827" }}>{fmtINR(po.costINR)}</span>
                </div>
                <div style={{ fontSize: 10, color: "#9ca3af", marginBottom: 10 }}>
                  {po.partId} · Qty {po.qty} · {po.lead} · {po.equipment}
                </div>
                <POTracker status={po.status} />
                <div style={{ marginTop: 10, display: "flex", justifyContent: "flex-end" }}>
                  {po.status === "Pending"  && (
                    <button onClick={() => advancePO(po.id)}
                      style={{ fontSize: 11, fontWeight: 700, padding: "5px 14px", borderRadius: 6, background: "#eff6ff", color: "#2563eb", border: "1px solid #bfdbfe", cursor: "pointer" }}>
                      Approve PO
                    </button>
                  )}
                  {po.status === "Approved" && (
                    <button onClick={() => advancePO(po.id)}
                      style={{ fontSize: 11, fontWeight: 700, padding: "5px 14px", borderRadius: 6, background: "#f5f3ff", color: "#7c3aed", border: "1px solid #ddd6fe", cursor: "pointer" }}>
                      Mark Shipped
                    </button>
                  )}
                  {po.status === "Shipped"  && (
                    <button onClick={() => advancePO(po.id)}
                      style={{ fontSize: 11, fontWeight: 700, padding: "5px 14px", borderRadius: 6, background: "#f0fdf4", color: "#065f46", border: "1px solid #bbf7d0", cursor: "pointer" }}>
                      Receive
                    </button>
                  )}
                  {po.status === "Received" && (
                    <span style={{ fontSize: 11, fontWeight: 700, color: "#10b981", display: "flex", alignItems: "center", gap: 4 }}>
                      <CheckCircle2 size={13} /> Received
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Spend summary */}
          <div style={{ padding: "14px 16px", borderTop: "1px solid #f1f5f9", background: "#f8fafc" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                { label: "Total PO Spend",  value: fmtINR(totalSpend), color: "#111827" },
                { label: "On-Order (Open)", value: fmtINR(openSpend),  color: "#ef4444" },
              ].map(m => (
                <div key={m.label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#9ca3af" }}>{m.label}</div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: m.color }}>{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
