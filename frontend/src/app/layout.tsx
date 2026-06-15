import type { Metadata } from "next";
import { Suspense } from "react";
import "./globals.css";
import HideDevTools from "@/components/HideDevTools";
import TopNav from "@/components/TopNav";

export const metadata: Metadata = {
  title: "STELOS | Autonomous Maintenance Intelligence",
  description: "AI-powered predictive maintenance for industrial operations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body style={{ background: "#f8fafc", color: "#111827", height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden", fontFamily: "Inter, -apple-system, sans-serif" }}>
        <HideDevTools />
        <Suspense fallback={null}>
          <TopNav />
        </Suspense>
        <main style={{ flex: 1, overflowY: "auto", background: "#f8fafc" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
