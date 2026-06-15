"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutGrid, TrendingUp, ShieldAlert,
  MessageSquare, FlaskConical, Activity,
  Cpu, Circle,
} from "lucide-react";

const NAV = [
  {
    section: "MONITORING",
    items: [
      { href: "/",          label: "Fleet Assets",  Icon: LayoutGrid   },
      { href: "/executive", label: "Executive",     Icon: TrendingUp   },
      { href: "/risk",      label: "Risk Center",   Icon: ShieldAlert  },
    ],
  },
  {
    section: "AI TOOLS",
    items: [
      { href: "/console",  label: "AI Copilot",   Icon: MessageSquare },
      { href: "/whatif",   label: "What-If Sim",  Icon: FlaskConical  },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside style={{
      width: 185,
      flexShrink: 0,
      background: "#ffffff",
      borderRight: "1px solid #e5e7eb",
      display: "flex",
      flexDirection: "column",
      height: "100vh",
    }}>

      {/* Logo */}
      <div style={{ padding: "18px 16px 16px", borderBottom: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6,
            background: "#2563eb",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Cpu size={14} color="#fff" />
          </div>
          <div>
            <div style={{ color: "#111827", fontSize: 13, fontWeight: 700, letterSpacing: 0.3, lineHeight: 1.1 }}>STELOS</div>
            <div style={{ color: "#6b7280", fontSize: 9, fontWeight: 600, letterSpacing: 2, marginTop: 2 }}>AI PLATFORM</div>
          </div>
        </div>
      </div>

      {/* Live badge */}
      <div style={{ padding: "8px 16px", borderBottom: "1px solid #f3f4f6" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Circle size={6} fill="#10b981" color="#10b981" style={{ flexShrink: 0 }} />
          <span style={{ color: "#10b981", fontSize: 10, fontWeight: 600, letterSpacing: 0.5 }}>Live</span>
          <span style={{ color: "#6b7280", fontSize: 10 }}>· 10 assets</span>
        </div>
      </div>

      {/* Nav */}
      <div style={{ flex: 1, overflowY: "auto", padding: "12px 8px" }}>
        {NAV.map(({ section, items }) => (
          <div key={section} style={{ marginBottom: 20 }}>
            {/* Section label */}
            <div style={{
              color: "#6b7280",
              fontSize: 9, fontWeight: 700,
              letterSpacing: 2,
              padding: "0 8px",
              marginBottom: 4,
            }}>
              {section}
            </div>

            {/* Items */}
            {items.map(({ href, label, Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 9,
                    padding: "8px 8px",
                    borderRadius: 5,
                    marginBottom: 1,
                    textDecoration: "none",
                    color: active ? "#2563eb" : "#6b7280",
                    background: active ? "#eff6ff" : "transparent",
                    fontSize: 13,
                    fontWeight: active ? 500 : 400,
                    transition: "background 0.12s, color 0.12s",
                  }}
                  onMouseEnter={e => {
                    if (!active) {
                      (e.currentTarget as HTMLElement).style.background = "#f8fafc";
                      (e.currentTarget as HTMLElement).style.color = "#111827";
                    }
                  }}
                  onMouseLeave={e => {
                    if (!active) {
                      (e.currentTarget as HTMLElement).style.background = "transparent";
                      (e.currentTarget as HTMLElement).style.color = "#6b7280";
                    }
                  }}
                >
                  <Icon
                    size={13}
                    style={{
                      flexShrink: 0,
                      color: active ? "#2563eb" : "inherit",
                      opacity: active ? 1 : 0.75,
                    }}
                  />
                  {label}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      {/* Footer status */}
      <div style={{ padding: "12px 16px", borderTop: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
          <Activity size={10} style={{ color: "#2563eb" }} />
          <span style={{ color: "#6b7280", fontSize: 10, fontWeight: 500 }}>AI Active</span>
        </div>
        <div style={{ color: "#6b7280", fontSize: 9, letterSpacing: 0.5 }}>Tata Steel · Hackathon 2026</div>
      </div>
    </aside>
  );
}
