"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { FileText, Mail, Download, X, CheckCircle2, Loader2 } from "lucide-react";
import { useFleet, FleetAsset } from "@/lib/fleetStore";

const NAV = [
  { href: "/",            label: "Assets"           },
  { href: "/console",     label: "AI Copilot"       },
  { href: "/executive",   label: "War Room"         },
  { href: "/plantmap",    label: "Plant Map"        },
  { href: "/risk",        label: "Risk Center"      },
  { href: "/whatif",      label: "What-If"          },
  { href: "/procurement", label: "Procurement"      },
  { href: "/ops",         label: "Maintenance Hub"  },
];

// ─── Report HTML generator (used for both PDF window and email) ────
function buildReportHTML(to: string, ts: string, fleet: FleetAsset[]) {
  const sorted     = [...fleet].sort((a, b) => b.failure_probability - a.failure_probability);
  const critical   = fleet.filter(e => e.alert_level === "CRITICAL");
  const warnings   = fleet.filter(e => e.alert_level === "WARNING");
  const avgHealth  = fleet.length ? (fleet.reduce((s, e) => s + e.health_score, 0) / fleet.length).toFixed(1) : "—";

  const SOP_MAP: Record<string, { action: string; sop: string }> = {
    "Pump-B":        { action: "Initiate controlled shutdown — bearing failure imminent. Flush lubrication system.", sop: "SOP-EMERGENCY-001 §3.1" },
    "Blast-Furnace": { action: "FFT vibration spectrum analysis. Inspect tuyere assembly for wear.",               sop: "SOP-VIBRATION-001 §2.2" },
    "Conveyor-B":    { action: "Vibration spectrum analysis. Schedule bearing replacement within RUL window.",     sop: "SOP-BEARING-001 §4.3"  },
    "Rolling-Mill":  { action: "Roll surface inspection. Check alignment and coupling condition.",                  sop: "SOP-ALIGNMENT-001 §2"  },
  };

  const alertRows = sorted.map(e => {
    const cls   = e.alert_level === "CRITICAL" ? "crit" : e.alert_level === "WARNING" ? "warn" : "norm";
    const rul   = e.predicted_rul_days != null ? `${e.predicted_rul_days.toFixed(1)}d` : "—";
    const fp    = `${Math.round(e.failure_probability * 100)}%`;
    const pri   = e.maintenance_priority ?? "—";
    return `<tr>
      <td><b>${e.equipment_id}</b></td>
      <td>${e.location}</td>
      <td><span class="badge ${cls}">${e.alert_level}</span></td>
      <td>${Math.round(e.health_score)}%</td>
      <td>${rul}</td>
      <td>${fp}</td>
      <td><span class="badge ${cls}">${pri}</span></td>
    </tr>`;
  }).join("");

  const actionAssets = sorted.filter(e => e.alert_level !== "NORMAL");
  const actionRows = actionAssets.map(e => {
    const cls = e.alert_level === "CRITICAL" ? "crit" : "warn";
    const pri = e.maintenance_priority ?? "—";
    const sop = SOP_MAP[e.equipment_id] ?? { action: `Inspect ${e.type} — elevated failure risk detected.`, sop: "SOP-GENERAL-001" };
    return `<tr>
      <td><span class="badge ${cls}">${pri}</span></td>
      <td>${e.equipment_id}</td>
      <td>${sop.action}</td>
      <td>${sop.sop}</td>
    </tr>`;
  }).join("");

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>STELOS Plant Status Report</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; background:#f8fafc; color:#1d1d1f; }
  .wrap { max-width:860px; margin:0 auto; padding:40px 32px; }
  .header { border-bottom:3px solid #0071e3; padding-bottom:20px; margin-bottom:28px; }
  .logo { font-size:36px; font-weight:900; letter-spacing:4px; color:#0071e3; }
  .sub { font-size:11px; letter-spacing:3px; color:#6e6e73; text-transform:uppercase; margin-top:4px; }
  .meta { font-size:12px; color:#6e6e73; margin-top:8px; }
  .kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:28px; }
  .kpi { background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:16px; text-align:center; }
  .kpi-label { font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#9ca3af; margin-bottom:8px; }
  .kpi-val { font-size:28px; font-weight:800; }
  .section-title { font-size:11px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#6e6e73; margin-bottom:12px; }
  table { width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden; border:1px solid #e5e7eb; margin-bottom:28px; }
  th { background:#f8fafc; font-size:10px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#6e6e73; padding:10px 14px; text-align:left; border-bottom:1px solid #e5e7eb; }
  td { padding:10px 14px; font-size:12px; border-bottom:1px solid #f1f5f9; }
  tr:last-child td { border-bottom:none; }
  .badge { display:inline-block; padding:2px 8px; border-radius:20px; font-size:10px; font-weight:700; }
  .crit { background:#fef2f2; color:#dc2626; }
  .warn { background:#fffbeb; color:#d97706; }
  .norm { background:#f0fdf4; color:#16a34a; }
  .footer { text-align:center; font-size:11px; color:#9ca3af; border-top:1px solid #e5e7eb; padding-top:20px; margin-top:28px; }
  @media print {
    body { background:#fff; }
    .wrap { padding:20px; }
    * { color:#111827 !important; background:#fff !important; border-color:#d1d5db !important; box-shadow:none !important; }
    .badge { border:1px solid #6b7280 !important; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo">STELOS</div>
    <div class="sub">Autonomous Maintenance Intelligence · Tata Steel</div>
    <div class="meta">Generated: ${ts} &nbsp;·&nbsp; Recipient: ${to}</div>
  </div>

  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-label">Fleet Health</div><div class="kpi-val">${avgHealth}%</div></div>
    <div class="kpi"><div class="kpi-label">Critical Assets</div><div class="kpi-val">${critical.length}</div></div>
    <div class="kpi"><div class="kpi-label">Warnings</div><div class="kpi-val">${warnings.length}</div></div>
    <div class="kpi"><div class="kpi-label">Assets Monitored</div><div class="kpi-val">${fleet.length}</div></div>
  </div>

  <div class="section-title">All Equipment — Live Snapshot</div>
  <table>
    <thead><tr><th>Machine</th><th>Location</th><th>Status</th><th>Health</th><th>RUL</th><th>Fail Risk</th><th>Priority</th></tr></thead>
    <tbody>${alertRows}</tbody>
  </table>

  <div class="section-title">Immediate Actions Required</div>
  <table>
    <thead><tr><th>Priority</th><th>Machine</th><th>Action</th><th>SOP Reference</th></tr></thead>
    <tbody>${actionRows || '<tr><td colspan="4" style="text-align:center;color:#16a34a">No active alerts — fleet is stable</td></tr>'}</tbody>
  </table>

  <div class="footer">
    STELOS · AI-Powered Predictive Maintenance · Tata Steel Hackathon 2026<br/>
    LangGraph · XGBoost · Weibull RUL · FAISS RAG · Isolation Forest
  </div>
</div>
</body>
</html>`;
}

// ─── Report Modal ─────────────────────────────────────────────────
function ReportModal({ onClose }: { onClose: () => void }) {
  const fleet = useFleet();
  const [emailTo, setEmailTo]   = useState("varshithdara@gmail.com");
  const [sending, setSending]   = useState(false);
  const [sent, setSent]         = useState(false);
  const [error, setError]       = useState("");

  const ts = new Date().toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

  const critical  = fleet.filter(e => e.alert_level === "CRITICAL").length;
  const warnings  = fleet.filter(e => e.alert_level === "WARNING").length;
  const avgHealth = fleet.length ? (fleet.reduce((s, e) => s + e.health_score, 0) / fleet.length).toFixed(1) : "—";

  const downloadPDF = () => {
    const html = buildReportHTML(emailTo, ts, fleet);
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => { w.print(); }, 600);
  };

  const sendEmail = async () => {
    setSending(true);
    setError("");
    try {
      const res = await fetch("/api/send-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: emailTo, timestamp: ts, html: buildReportHTML(emailTo, ts, fleet) }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Failed to send");
      }
      setSent(true);
    } catch (e: any) {
      setError(e.message || "Email failed — check backend GMAIL credentials.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(0,0,0,0.35)", backdropFilter: "blur(4px)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }} onClick={onClose}>
      <div style={{
        background: "#ffffff", borderRadius: 16, padding: "28px 32px",
        width: 480, boxShadow: "0 20px 60px rgba(0,0,0,0.18)",
        border: "1px solid #e5e7eb",
      }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: "#eff6ff", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <FileText size={18} color="#2563eb" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: "#1d1d1f" }}>Plant Status Report</div>
              <div style={{ fontSize: 11, color: "#9ca3af" }}>{ts}</div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#9ca3af" }}>
            <X size={18} />
          </button>
        </div>

        {/* Report summary */}
        <div style={{ background: "#f8fafc", border: "1px solid #e5e7eb", borderRadius: 12, padding: "16px 20px", marginBottom: 20 }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 2, color: "#9ca3af", textTransform: "uppercase", marginBottom: 12 }}>Report Includes</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {[
              ["Fleet Health", `${avgHealth}% avg across ${fleet.length} assets`],
              ["Critical Alerts", `${critical} machine${critical !== 1 ? "s" : ""} — P1 action required`],
              ["Warning Assets", `${warnings} machine${warnings !== 1 ? "s" : ""} — P2 scheduled`],
              ["Action Items", `${critical + warnings} maintenance task${critical + warnings !== 1 ? "s" : ""} listed`],
            ].map(([label, val]) => (
              <div key={label} style={{ fontSize: 12 }}>
                <div style={{ fontWeight: 600, color: "#374151" }}>{label}</div>
                <div style={{ color: "#6b7280", fontSize: 11 }}>{val}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Email recipient */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: "#6b7280", textTransform: "uppercase", marginBottom: 8 }}>Send To</div>
          <input
            value={emailTo}
            onChange={e => { setEmailTo(e.target.value); setSent(false); setError(""); }}
            placeholder="official@tatasteel.com"
            style={{
              width: "100%", padding: "10px 14px", borderRadius: 8, fontSize: 13,
              border: "1px solid #e5e7eb", background: "#f8fafc", color: "#1d1d1f",
              outline: "none",
            }}
          />
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#dc2626", marginBottom: 16 }}>
            {error}
          </div>
        )}

        {/* Success */}
        {sent && (
          <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "10px 14px", fontSize: 12, color: "#16a34a", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <CheckCircle2 size={14} /> Report emailed to {emailTo}
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={downloadPDF} style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            padding: "11px 0", borderRadius: 10, fontSize: 13, fontWeight: 600,
            background: "#ffffff", border: "1px solid #e5e7eb", color: "#374151", cursor: "pointer",
          }}>
            <Download size={15} /> Download PDF
          </button>
          <button onClick={sendEmail} disabled={sending || !emailTo} style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            padding: "11px 0", borderRadius: 10, fontSize: 13, fontWeight: 600,
            background: sending ? "#93c5fd" : "#2563eb", color: "#fff", border: "none", cursor: sending ? "default" : "pointer",
            opacity: !emailTo ? 0.5 : 1,
          }}>
            {sending ? <Loader2 size={15} className="animate-spin" /> : <Mail size={15} />}
            {sending ? "Sending…" : "Email Report"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── TopNav ───────────────────────────────────────────────────────
export default function TopNav() {
  const pathname = usePathname();
  const [clock, setClock] = useState("");
  const [tick, setTick] = useState(0);
  const [reportOpen, setReportOpen] = useState(false);

  useEffect(() => {
    const update = () => setClock(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    update();
    const id = setInterval(() => { update(); setTick(t => t + 1); }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <header style={{
        height: 64,
        background: "#ffffff",
        borderBottom: "1px solid #e5e7eb",
        display: "flex",
        alignItems: "center",
        padding: "0 40px",
        gap: 0,
        flexShrink: 0,
        position: "relative",
        zIndex: 50,
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", marginRight: 48 }}>
          <div style={{
            fontFamily: "'Bebas Neue', Impact, sans-serif",
            fontSize: 28,
            letterSpacing: 4,
            color: "#111827",
            lineHeight: 1,
          }}>STELOS</div>
        </div>

        {/* Nav items */}
        <nav style={{ display: "flex", alignItems: "center", gap: 4, flex: 1 }}>
          {NAV.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href} style={{
                padding: "8px 18px",
                fontSize: 14,
                fontWeight: active ? 600 : 400,
                color: active ? "#2563eb" : "#6b7280",
                textDecoration: "none",
                borderRadius: 4,
                background: active ? "#eff6ff" : "transparent",
                borderBottom: active ? "2px solid #2563eb" : "2px solid transparent",
                transition: "all 0.15s ease",
                whiteSpace: "nowrap" as const,
              }}
                onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#111827"; }}
                onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.color = "#6b7280"; }}
              >
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Right side — report button + clock */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginLeft: "auto" }}>
          <button
            onClick={() => setReportOpen(true)}
            title="Export & Email Status Report"
            style={{
              display: "flex", alignItems: "center", gap: 7,
              padding: "7px 16px", borderRadius: 6, fontSize: 13, fontWeight: 600,
              background: "#eff6ff", border: "1px solid #bfdbfe", color: "#2563eb",
              cursor: "pointer", letterSpacing: 0.3,
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "#dbeafe"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "#eff6ff"; }}
          >
            <FileText size={15} />
            Report
          </button>
          <span style={{
            color: "#374151",
            fontSize: 14,
            fontFamily: "'Inter', -apple-system, sans-serif",
            fontWeight: 500,
            letterSpacing: 0.5,
          }}>{clock}</span>
        </div>
      </header>

      {reportOpen && <ReportModal onClose={() => setReportOpen(false)} />}
    </>
  );
}
