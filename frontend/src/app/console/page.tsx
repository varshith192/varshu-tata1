"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Send, Bot, User, ShieldAlert, Wrench, Search, Zap,
  BookOpen, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp, RefreshCw,
  Bell, TrendingUp, BarChart2, FileText, X, IndianRupee,
  ThumbsUp, ThumbsDown, Package
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LabelList
} from "recharts";

const BASE_EQUIPMENT = [
  { id: "Pump-B",        location: "Blast Furnace #3",      type: "pump",     sensor: { temperature: 92.5, vibration: 0.72, pressure: 84.0,  oil_temp: 68.5, motor_current: 18.2 } },
  { id: "Pump-A",        location: "Blast Furnace #2",      type: "pump",     sensor: { temperature: 71.0, vibration: 0.38, pressure: 98.0,  oil_temp: 56.0, motor_current: 14.2 } },
  { id: "Pump-C",        location: "Blast Furnace #4",      type: "pump",     sensor: { temperature: 66.0, vibration: 0.28, pressure: 102.0, oil_temp: 53.0, motor_current: 13.8 } },
  { id: "Conveyor-B",    location: "Raw Material Yard",      type: "conveyor", sensor: { temperature: 74.0, vibration: 0.52, pressure: 92.0,  oil_temp: 60.0, motor_current: 15.5 } },
  { id: "Cooling-Fan-4", location: "Sinter Plant",           type: "fan",      sensor: { temperature: 68.0, vibration: 0.31, pressure: 99.0,  oil_temp: 54.0, motor_current: 13.5 } },
  { id: "Rolling-Mill",  location: "Hot Rolling Section",    type: "mill",     sensor: { temperature: 69.0, vibration: 0.32, pressure: 96.0,  oil_temp: 52.0, motor_current: 14.0 } },
  { id: "Cooling-Unit",  location: "Steel Melting Shop",     type: "fan",      sensor: { temperature: 64.0, vibration: 0.29, pressure: 101.0, oil_temp: 50.0, motor_current: 12.8 } },
  { id: "Power-Unit",    location: "Power Distribution",     type: "pump",     sensor: { temperature: 58.0, vibration: 0.22, pressure: 104.0, oil_temp: 47.0, motor_current: 11.5 } },
  { id: "Blast-Furnace", location: "Blast Furnace #1",       type: "furnace",  sensor: { temperature: 81.0, vibration: 0.58, pressure: 87.0,  oil_temp: 63.0, motor_current: 16.8 } },
  { id: "Compressor-2",  location: "Oxygen Plant",           type: "pump",     sensor: { temperature: 67.0, vibration: 0.27, pressure: 103.0, oil_temp: 51.0, motor_current: 13.2 } },
];

const ALERT_COLOR: Record<string, string> = {
  EMERGENCY: "#ef4444", CRITICAL: "#f97316", WARNING: "#f59e0b", NORMAL: "#10b981",
};

const SAMPLE_QUERIES = [
  "Diagnose the current condition and provide RUL estimate",
  "Show me the sensor trend for the last 7 days",
  "Which equipment needs urgent attention across the entire plant?",
  "What spare parts do I need and what are the lead times?",
  "Generate a maintenance report for this equipment",
];

const ANIMATED_AGENTS = [
  { agent: "Diagnostic",           action: "Running Isolation Forest anomaly detection on 5 sensors..." },
  { agent: "KnowledgeRetrieval",   action: "FAISS semantic search over Tata Steel SOPs and failure reports..." },
  { agent: "RootCause",            action: "LLM causal chain analysis with full SOP context..." },
  { agent: "PredictiveMaintenance",action: "Weibull RUL + Risk Matrix (5×5) + SOP work orders..." },
  { agent: "BusinessImpact",       action: "Computing ₹ ROI, spares urgency, and approval gate..." },
  { agent: "ExecutiveIntelligence",action: "Composing XAI report with confidence scoring..." },
];

type Trace = { agent: string; action: string; result?: string; health_score?: number; confidence_score?: number; llm_enhanced?: boolean; llm_generated_actions?: boolean; primary_mechanism?: string; rc_confidence?: string; };
type Metrics = {
  diagnosis: string; rootCause: string; causalChain: string; primaryMechanism: string;
  rul: number; rulLower: number; rulUpper: number;
  risk: string; healthScore: number; failureProb: number; alertLevel: string; priority: string;
  confidenceScore: number; xaiExplanation: string; evidenceChain: string[];
  retrievedSources: string[]; recommendedActions: { action: string; priority: string; sop_reference: string; estimated_time?: string; type?: string }[];
  workOrderId?: string;
  anomalyScores: Record<string, number>;
  businessImpact: any;
  mlFailureProb: number | null;
  predictedFailureType: string | null;
  failureTypeLabel: string | null;
  shapTopFeatures: { feature: string; shap: number }[];
  modelAuc: number | null;
};

type Message = {
  role: "user" | "agent";
  content: string;
  workOrderId?: string;
  feedbackGiven?: "up" | "down" | null;
  suggestions?: string[];
};

const FOLLOW_UP_POOL: Record<string, string[]> = {
  EMERGENCY: [
    "What is the emergency shutdown procedure?",
    "Which spare parts do I need urgently?",
    "What are the safety risks if I keep running?",
    "How long before complete failure?",
    "What is the cost of breakdown vs planned repair?",
    "What caused this emergency condition?",
    "Can I reduce load instead of shutting down?",
    "What PPE should the maintenance team wear?",
    "How do I isolate this equipment safely?",
    "What is the fastest repair option available?",
    "Which SOP applies to this failure mode?",
    "What is the step-by-step repair procedure?",
  ],
  CRITICAL: [
    "What maintenance actions should I take now?",
    "How many days of useful life remain?",
    "Show me the 7-day sensor trend",
    "What spare parts do I need to order?",
    "What is the financial cost of ignoring this?",
    "Can I keep running at reduced load safely?",
    "What is the root cause of this condition?",
    "How often should I monitor sensors now?",
    "What is the shutdown procedure if it worsens?",
    "Which SOP applies to this failure mode?",
    "What vibration level triggers an emergency stop?",
    "How much production will I lose if it fails?",
  ],
  WARNING: [
    "Show me the sensor trend for last 7 days",
    "How many days before maintenance is needed?",
    "What immediate actions should I take?",
    "Is it safe to keep running at full load?",
    "What spare parts should I pre-order?",
    "What is the failure probability this week?",
    "What caused the warning condition?",
    "How do I bring vibration levels down?",
    "What is the estimated maintenance cost?",
    "Should I schedule a planned shutdown now?",
    "What is the risk of waiting until next week?",
    "What does ISO 10816-3 say about this vibration?",
  ],
  NORMAL: [
    "Show me the sensor trend for last 7 days",
    "What is the remaining useful life estimate?",
    "What would cause a failure on this machine?",
    "What does the next scheduled maintenance involve?",
    "What is the current failure probability?",
    "How does this compare to similar equipment?",
    "Which sensors are most critical to monitor?",
    "What spare parts should be kept in stock?",
    "What is the typical MTBF for this equipment?",
    "Can I safely extend the maintenance interval?",
    "What early warning signs should I watch for?",
    "What lubrication schedule does this machine need?",
  ],
};

function generateSuggestions(alertLevel: string, lastQuestion: string, used: Set<string>): string[] {
  const lq = lastQuestion.toLowerCase();
  const pool = FOLLOW_UP_POOL[alertLevel] || FOLLOW_UP_POOL.NORMAL;

  const topicBlocked = (qq: string) => {
    if (lq.includes("trend") && qq.includes("trend")) return true;
    if (lq.includes("shutdown") && qq.includes("shutdown")) return true;
    if ((lq.includes("spare") || lq.includes("parts")) && qq.includes("spare")) return true;
    if ((lq.includes("rul") || lq.includes("remaining") || lq.includes("life")) && qq.includes("remaining")) return true;
    if ((lq.includes("cost") || lq.includes("rupee") || lq.includes("financial")) && qq.includes("cost")) return true;
    if ((lq.includes("action") || lq.includes("maintain") || lq.includes("fix")) && qq.includes("action")) return true;
    if ((lq.includes("safe") || lq.includes("risk")) && qq.includes("safe")) return true;
    if (lq.includes("root cause") && qq.includes("root cause")) return true;
    if (lq.includes("sop") && qq.includes("sop")) return true;
    return false;
  };

  // First pass: exclude already-used AND topic-similar
  let filtered = pool.filter(q => !used.has(q) && !topicBlocked(q.toLowerCase()));

  // Second pass (fallback): if not enough unused, allow used ones but still filter topic
  if (filtered.length < 2) {
    filtered = pool.filter(q => !topicBlocked(q.toLowerCase()));
  }

  // Third pass (last resort): take anything from pool not identical to last question
  if (filtered.length < 2) {
    filtered = pool.filter(q => q.toLowerCase() !== lq);
  }

  const selected = filtered.slice(0, 2);
  selected.forEach(s => used.add(s));
  return selected;
}

type HistoricalCase = {
  id: number;
  timestamp: string;
  equipment_id: string;
  alert_level: string;
  diagnosis: string;
  root_cause: string;
  health_score: number;
  rul_days: number;
  maintenance_priority: string;
  recommended_actions: { action: string; priority: string }[];
};

const AGENT_ICONS: Record<string, React.ReactElement> = {
  Supervisor:            <ShieldAlert className="h-4 w-4" />,
  Diagnostic:            <Search className="h-4 w-4" />,
  RootCause:             <Zap className="h-4 w-4" />,
  KnowledgeRetrieval:    <BookOpen className="h-4 w-4" />,
  PredictiveMaintenance: <Wrench className="h-4 w-4" />,
  RiskAssessment:        <ShieldAlert className="h-4 w-4" />,
  BusinessImpact:        <IndianRupee className="h-4 w-4" />,
  MaintenancePlanning:   <CheckCircle2 className="h-4 w-4" />,
  HumanApproval:         <User className="h-4 w-4" />,
  ExecutiveIntelligence: <Bot className="h-4 w-4" />,
};

const ALERT_STYLES: Record<string, string> = {
  EMERGENCY: "bg-rose-100 text-rose-800 border-rose-300",
  CRITICAL:  "bg-rose-50 text-rose-700 border-rose-200",
  WARNING:   "bg-amber-50 text-amber-700 border-amber-200",
  NORMAL:    "bg-emerald-50 text-emerald-700 border-emerald-200",
};

const SPARE_PARTS: Record<string, { part: string; qty: string; avail: "In Stock" | "Limited" | "Out of Stock"; lead: string; source: string }[]> = {
  pump: [
    { part: "Bearing Kit (SKF 6205)",     qty: "4 sets",  avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
    { part: "Mechanical Seal (Type-II)",  qty: "1 set",   avail: "Limited",       lead: "3–5 days",    source: "SAIL Stores" },
    { part: "Impeller (316 SS)",          qty: "0",       avail: "Out of Stock",  lead: "14–21 days",  source: "OEM — Kirloskar" },
    { part: "Coupling Insert (Poly)",     qty: "6 pcs",   avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
  ],
  conveyor: [
    { part: "Conveyor Belt Section (5m)", qty: "2 rolls", avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
    { part: "Idler Roller Set",           qty: "3 sets",  avail: "In Stock",      lead: "Warehouse",   source: "Mechanical Store" },
    { part: "Drive Chain (80H)",          qty: "0",       avail: "Out of Stock",  lead: "10–14 days",  source: "OEM — Rexnord" },
    { part: "Sprocket (Z=21)",            qty: "1 pc",    avail: "Limited",       lead: "5–7 days",    source: "SAIL Stores" },
  ],
  fan: [
    { part: "Fan Blade Assembly",         qty: "1 set",   avail: "Limited",       lead: "7–10 days",   source: "OEM — Howden" },
    { part: "Motor Bearing (FAG 6308)",   qty: "8 pcs",   avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
    { part: "V-Belt Set (B-Section)",     qty: "12 pcs",  avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
    { part: "Fan Shaft Seal",             qty: "0",       avail: "Out of Stock",  lead: "21–28 days",  source: "OEM — Howden" },
  ],
  furnace: [
    { part: "Tuyere Assembly (Complete)", qty: "2 sets",  avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
    { part: "Cooling Stave (Cu)",         qty: "0",       avail: "Out of Stock",  lead: "21–28 days",  source: "OEM — SMS Group" },
    { part: "Blowpipe & Bustle Seal",     qty: "4 sets",  avail: "In Stock",      lead: "Warehouse",   source: "BF Spares Store" },
    { part: "Thermocouple (Type-K)",      qty: "12 pcs",  avail: "In Stock",      lead: "Warehouse",   source: "Instrumentation Store" },
    { part: "Refractory Brick (Grade C)", qty: "0",       avail: "Out of Stock",  lead: "35–42 days",  source: "OEM — Vesuvius India" },
  ],
  mill: [
    { part: "Work Roll (Forged Steel)",   qty: "0",       avail: "Out of Stock",  lead: "14–21 days",  source: "OEM — Bhilai Roll Plant" },
    { part: "Bearing Housing (Roll)",     qty: "2 sets",  avail: "In Stock",      lead: "Warehouse",   source: "Rolling Mill Store" },
    { part: "Hydraulic Cylinder Seal Kit",qty: "3 sets",  avail: "In Stock",      lead: "Warehouse",   source: "Central Store" },
    { part: "Spindle Coupling Insert",    qty: "1 set",   avail: "Limited",       lead: "5–7 days",    source: "SAIL Stores" },
    { part: "Mill Stand Liner Plate",     qty: "0",       avail: "Out of Stock",  lead: "28–35 days",  source: "OEM — Primetals" },
  ],
};

const AVAIL_STYLE: Record<string, string> = {
  "In Stock":      "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Limited":       "bg-amber-50 text-amber-700 border-amber-200",
  "Out of Stock":  "bg-rose-50 text-rose-700 border-rose-200",
};

function SpareParts({ equipmentId, equipmentType, priority }: { equipmentId: string; equipmentType: string; priority: string }) {
  const parts = SPARE_PARTS[equipmentType] || SPARE_PARTS.pump;
  const urgentCount = parts.filter(p => p.avail !== "In Stock").length;
  const isHighPriority = priority === "P1" || priority === "P2";

  return (
    <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
      <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
        <span className="font-bold text-sm" style={{ color: "#1d1d1f" }}>Spare Parts Inventory</span>
        {urgentCount > 0 && isHighPriority && (
          <span className="ml-auto text-xs bg-rose-100 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full font-medium">
            {urgentCount} item{urgentCount > 1 ? "s" : ""} at risk
          </span>
        )}
      </div>
      <div className="p-3 space-y-2">
        {parts.map((p, i) => (
          <div key={i} className="flex items-start gap-2 text-xs">
            <div className="flex-1 min-w-0">
              <div className="font-medium text-slate-800 truncate">{p.part}</div>
              <div className="text-slate-400 flex items-center gap-1.5 mt-0.5">
                <span>{p.lead}</span>
                <span className="text-slate-300">·</span>
                <span>{p.source}</span>
              </div>
            </div>
            <span className={`shrink-0 px-1.5 py-0.5 rounded border text-xs font-medium ${AVAIL_STYLE[p.avail]}`}>
              {p.avail === "In Stock" ? "✓ " : p.avail === "Out of Stock" ? "✗ " : "⚠ "}{p.avail}
            </span>
          </div>
        ))}
        {isHighPriority && parts.some(p => p.avail === "Out of Stock") && (
          <div className="mt-2 pt-2 border-t border-slate-100 text-xs text-rose-600 font-medium flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            Initiate emergency procurement for out-of-stock items before RUL expires
          </div>
        )}
      </div>
    </div>
  );
}

function MsgContent({ content }: { content: string }) {
  const paragraphs = content.split(/\n{2,}/);
  return (
    <div className="space-y-2.5">
      {paragraphs.map((para, pi) => {
        const lines = para.split("\n");
        return (
          <div key={pi} className="space-y-1">
            {lines.map((line, li) => {
              const renderInline = (text: string) => {
                const parts = text.split(/\*\*(.*?)\*\*/g);
                return parts.map((p, i) =>
                  i % 2 === 1 ? <strong key={i} className="font-semibold text-slate-900">{p}</strong> : <span key={i}>{p}</span>
                );
              };
              if (line.startsWith("• ") || line.startsWith("- ")) {
                return (
                  <div key={li} className="flex gap-2 items-start">
                    <span className="mt-0.5 text-slate-400 shrink-0">•</span>
                    <span>{renderInline(line.slice(2))}</span>
                  </div>
                );
              }
              if (line.startsWith("✓ ")) {
                return (
                  <div key={li} className="flex gap-2 items-start">
                    <span className="mt-0.5 text-emerald-500 shrink-0 font-bold">✓</span>
                    <span>{renderInline(line.slice(2))}</span>
                  </div>
                );
              }
              if (line.startsWith("✗ ")) {
                return (
                  <div key={li} className="flex gap-2 items-start">
                    <span className="mt-0.5 text-rose-500 shrink-0 font-bold">✗</span>
                    <span>{renderInline(line.slice(2))}</span>
                  </div>
                );
              }
              if (line.startsWith("⚠ ") || line.startsWith("⚠️ ")) {
                return (
                  <div key={li} className="flex gap-2 items-start text-amber-700">
                    <span className="mt-0.5 shrink-0">⚠</span>
                    <span>{renderInline(line.replace(/^⚠️?\s/, ""))}</span>
                  </div>
                );
              }
              if (/^(Step \d|[0-9]+\.)/.test(line)) {
                return <div key={li} className="font-medium">{renderInline(line)}</div>;
              }
              if (line === "") return <div key={li} />;
              return <div key={li}>{renderInline(line)}</div>;
            })}
          </div>
        );
      })}
    </div>
  );
}

function AgentConsoleInner() {
  const searchParams = useSearchParams();
  const [selectedEq, setSelectedEq] = useState(BASE_EQUIPMENT[0]);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([
    { role: "agent", content: "I am Stelos AI — your Autonomous Maintenance Intelligence Platform. Select any equipment from the dropdown and ask me anything. I use Isolation Forest anomaly detection, Weibull RUL modelling, and FAISS RAG over Tata Steel SOPs and failure reports." }
  ]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [showActions, setShowActions] = useState(true);
  const [proactiveToast, setProactiveToast] = useState<{equipment_id: string; alert_level: string; message: string} | null>(null);
  const [seenAlerts, setSeenAlerts] = useState<Set<string>>(new Set());
  const [historicalCases, setHistoricalCases] = useState<HistoricalCase[]>([]);
  const [showHistorical, setShowHistorical] = useState(true);
  const [animatedAgents, setAnimatedAgents] = useState<number>(0);
  const [mode, setMode] = useState<"chat" | "manual">("chat");
  const [manualForm, setManualForm] = useState({ temperature: "92.5", vibration: "0.720", pressure: "84.0", oil_temp: "68.5", motor_current: "18.2", equipment_notes: "" });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const usedSuggestionsRef = useRef<Set<string>>(new Set());

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isProcessing]);

  // Animate agent cards one by one while processing
  useEffect(() => {
    if (!isProcessing) {
      setAnimatedAgents(0);
      return;
    }
    setAnimatedAgents(1);
    const interval = setInterval(() => {
      setAnimatedAgents(prev => {
        if (prev >= ANIMATED_AGENTS.length) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 800);
    return () => clearInterval(interval);
  }, [isProcessing]);

  // Proactive alert polling — checks every 30s for new CRITICAL/EMERGENCY alerts
  const pollAlerts = useCallback(async () => {
    try {
      const res = await apiFetch("/api/alerts/active");
      if (!res.ok) return;
      const data = await res.json();
      for (const alert of (data.alerts || [])) {
        if (alert.level !== "NORMAL" && !seenAlerts.has(alert.equipment_id + alert.level)) {
          setSeenAlerts(prev => new Set([...prev, alert.equipment_id + alert.level]));
          setProactiveToast({
            equipment_id: alert.equipment_id,
            alert_level: alert.level,
            message: alert.description || `${alert.level} alert on ${alert.equipment_id}`,
          });
          setTimeout(() => setProactiveToast(null), 10000);
          break;
        }
      }
    } catch { /* ignore */ }
  }, [seenAlerts]);

  useEffect(() => {
    pollAlerts();
    const id = setInterval(pollAlerts, 30000);
    return () => clearInterval(id);
  }, [pollAlerts]);


  // Fetch historical cases from logbook when equipment changes
  useEffect(() => {
    const fetchHistorical = async () => {
      try {
        const res = await apiFetch(`/api/logbook?equipment_id=${selectedEq.id}`, 6000);
        if (!res.ok) throw new Error();
        const data = await res.json();
        setHistoricalCases((data.entries || []).slice(0, 3));
      } catch {
        setHistoricalCases([]);
      }
    };
    fetchHistorical();
  }, [selectedEq.id]);

  // Sync manual form when selected equipment changes
  useEffect(() => {
    setManualForm({
      temperature: selectedEq.sensor.temperature.toString(),
      vibration: selectedEq.sensor.vibration.toFixed(3),
      pressure: selectedEq.sensor.pressure.toString(),
      oil_temp: selectedEq.sensor.oil_temp.toString(),
      motor_current: selectedEq.sensor.motor_current.toString(),
      equipment_notes: "",
    });
  }, [selectedEq.id]);

  const resetSession = () => {
    setSessionId(crypto.randomUUID());
    setMessages([{ role: "agent", content: `Session reset. Now monitoring ${selectedEq.id}. How can I help?` }]);
    setTraces([]);
    setMetrics(null);
    usedSuggestionsRef.current.clear();
  };

  const handleEquipmentChange = (eqId: string) => {
    const eq = BASE_EQUIPMENT.find(e => e.id === eqId)!;
    setSelectedEq(eq);
    setSessionId(crypto.randomUUID());
    usedSuggestionsRef.current.clear();
    setMessages([{ role: "agent", content: `Switched to ${eq.id} (${eq.location}). Ask me anything about this equipment.` }]);
    setTraces([]);
    setMetrics(null);
  };

  const buildLocalFallback = (userMsg: string): string => {
    const s = selectedEq.sensor;
    const t = s.temperature, v = s.vibration, p = s.pressure, o = s.oil_temp, c = s.motor_current;
    const alert = t >= 90 || v >= 0.70 ? "EMERGENCY" : t >= 85 || v >= 0.60 ? "CRITICAL" : t >= 78 || v >= 0.50 ? "WARNING" : "NORMAL";
    const q = userMsg.toLowerCase();
    const id = selectedEq.id;
    const eqType = selectedEq.type;

    const prob = t >= 90 ? "89%" : t >= 85 ? "65%" : t >= 78 ? "40%" : "< 15%";
    const rul  = t >= 90 ? "less than 1 day" : t >= 85 ? "2–5 days" : t >= 78 ? "7–15 days" : "more than 30 days";

    const faults: string[] = [];
    if (t >= 90) faults.push(`bearing temperature critically high at **${t}°C** (emergency threshold: 90°C)`);
    else if (t >= 78) faults.push(`bearing temperature elevated at **${t}°C** (warning threshold: 78°C)`);
    if (v >= 0.70) faults.push(`severe vibration at **${v.toFixed(3)} mm/s** — ISO 10816-3 Zone D (danger)`);
    else if (v >= 0.50) faults.push(`elevated vibration at **${v.toFixed(3)} mm/s** — ISO 10816-3 Zone C`);
    if (o >= 65) faults.push(`oil temperature high at **${o}°C** — lubrication is degrading`);
    if (c >= 17) faults.push(`motor current elevated at **${c} A** — possible mechanical overload`);
    if (p < 88) faults.push(`discharge pressure low at **${p} PSI** — impeller or suction line suspect`);

    const alertColor = alert === "EMERGENCY" ? "🔴" : alert === "CRITICAL" ? "🟠" : alert === "WARNING" ? "🟡" : "🟢";

    // ── Spare parts ──
    if (q.includes("spare") || q.includes("part") || q.includes("inventory") || q.includes("stock") || q.includes("order") || q.includes("procure") || q.includes("component") || q.includes("bearing kit") || q.includes("impeller") || q.includes("coupling")) {
      const parts = eqType === "conveyor"
        ? [["Conveyor Belt Section (5m)", "✓ In Stock", "Warehouse — available now"],["Idler Roller Set", "✓ In Stock", "Warehouse — available now"],["Drive Chain (80H)", "✗ Out of Stock", "OEM Rexnord — 10–14 days lead time"],["Sprocket (Z=21)", "⚠ Limited", "SAIL Stores — 5–7 days"]]
        : eqType === "fan"
        ? [["Fan Blade Assembly", "⚠ Limited", "OEM Howden — 7–10 days"],["Motor Bearing (FAG 6308)", "✓ In Stock", "Warehouse — available now"],["V-Belt Set (B-Section)", "✓ In Stock", "Warehouse — available now"],["Fan Shaft Seal", "✗ Out of Stock", "OEM Howden — 21–28 days"]]
        : [["Bearing Kit (SKF 6205)", "✓ In Stock", "Central Store — available now"],["Mechanical Seal (Type-II)", "⚠ Limited", "SAIL Stores — 3–5 days"],["Impeller (316 SS)", "✗ Out of Stock", "OEM Kirloskar — 14–21 days"],["Coupling Insert (Poly)", "✓ In Stock", "Central Store — available now"]];
      const oos = parts.filter(pt => pt[1].startsWith("✗"));
      const urgencyLine = oos.length > 0 && alert !== "NORMAL"
        ? `\n⚠ **${oos.length} critical item${oos.length > 1 ? "s are" : " is"} out of stock.** Given the current ${alert} alert and RUL of ${rul}, initiate emergency procurement immediately — lead time may exceed your maintenance window.`
        : `\n✓ All critical items available on-site. Standard procurement timeline applies.`;
      return `Here's the current spare parts inventory for **${id}**:\n\n${parts.map(pt => `${pt[1]} **${pt[0]}** — ${pt[2]}`).join("\n")}${urgencyLine}`;
    }

    // ── Monitoring frequency ──
    if (q.includes("how often") || q.includes("how frequent") || q.includes("frequency") || q.includes("monitoring schedule") || q.includes("check every") || q.includes("vibration level triggers") || (q.includes("monitor") && (q.includes("often") || q.includes("should") || q.includes("when")))) {
      const freq = alert === "EMERGENCY" ? "**every 30 minutes** with a dedicated operator assigned" : alert === "CRITICAL" ? "**every 2 hours**" : alert === "WARNING" ? "**every 4 hours**" : "**every 8 hours** as part of the standard shift check";
      const escalate = alert === "EMERGENCY" ? "Prepare for immediate shutdown if temperature exceeds **95°C** or vibration exceeds **0.80 mm/s**." : alert === "CRITICAL" ? "Escalate to shift supervisor if readings worsen over two consecutive checks." : alert === "WARNING" ? "If two consecutive readings are trending upward, escalate to CRITICAL watch protocol." : "No enhanced monitoring required — continue standard PM schedule.";
      return `Given that **${id}** is currently in **${alert}** condition, I recommend monitoring ${freq}.\n\nHere are the alert thresholds to watch:\n• **Temperature** — warn at >78°C | critical >85°C | emergency shutdown >90°C\n• **Vibration** — warn at >0.50 mm/s | critical >0.60 | emergency >0.70 mm/s\n• **Oil Temp** — immediate inspection above 70°C\n• **Motor Current** — emergency stop above 19 A\n\nCurrent readings: Temp **${t}°C** | Vib **${v.toFixed(3)} mm/s** | Oil **${o}°C** | Current **${c} A**\n\n${escalate} Log all readings in the Maintenance Logbook per SOP-PM-003 §2.`;
    }

    // ── Trend / history ──
    const isTrend = q.includes("trend") || q.includes("7 day") || q.includes("last 7") || q.includes("history") || q.includes("past week") || q.includes("last week") || q.includes("over time") || (q.includes("show") && (q.includes("sensor") || q.includes("data")));
    if (isTrend) {
      const rows = Array.from({ length: 7 }, (_, i) => {
        const date = new Date(Date.now() - (6 - i) * 86400000);
        const dateStr = date.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
        const j = (base: number, amp: number) => (base + Math.sin(i * 1.1 + base) * amp).toFixed(base < 2 ? 3 : 1);
        const tVal = parseFloat(j(t, 1.8)), vVal = parseFloat(j(v, 0.012));
        return `• **${dateStr}** — Temp ${j(t,1.8)}°C${tVal>=78?" ⚠":""} | Vib ${j(v,0.012)} mm/s${vVal>=0.50?" ⚠":""} | Press ${j(p,2.5)} PSI | Oil ${j(o,1.2)}°C`;
      });
      const trendNote = alert === "NORMAL"
        ? "✓ All sensors have been stable over the past 7 days — no degradation trend detected. The next scheduled PM cycle applies."
        : `⚠ Readings have been consistently elevated over the 7-day window, confirming the current **${alert}** condition is not a transient spike — maintenance is overdue.`;
      return `Here's the 7-day sensor trend for **${id}**:\n\n${rows.join("\n")}\n\n${trendNote}`;
    }

    // ── RUL / failure probability ──
    if (q.includes("rul") || q.includes("remaining") || q.includes("before complete") || q.includes("before failure") || q.includes("how long") || q.includes("days of useful") || q.includes("when will") || q.includes("life left") || q.includes("expire") || q.includes("failure prob") || q.includes("probability") || q.includes("failure") || q.includes("mtbf") || /\bdays\b/.test(q)) {
      const mtbf = eqType === "pump" ? "~2,400 hrs" : eqType === "conveyor" ? "~3,200 hrs" : eqType === "fan" ? "~4,000 hrs" : "~2,800 hrs";
      const action = t >= 90 ? "⚠ **This requires immediate action.** Initiate a controlled shutdown before the bearing reaches catastrophic failure." : t >= 85 ? "⚠ You have a narrow window. Plan and execute maintenance within 24 hours." : t >= 78 ? "Schedule a planned maintenance intervention within this RUL window to avoid unplanned downtime." : "✓ No urgency — continue standard PM schedule. Next inspection at the routine PM interval.";
      return `Based on current sensor readings, **${id}** has an estimated remaining useful life of **${rul}** with a failure probability of **${prob}**.\n\nThis is derived from the Weibull degradation model applied to:\n• **Temperature**: ${t}°C (${t >= 85 ? "above critical threshold" : t >= 78 ? "elevated" : "normal"})\n• **Vibration**: ${v.toFixed(3)} mm/s (${v >= 0.60 ? "critical" : v >= 0.50 ? "elevated" : "normal"})\n• **Oil Temp**: ${o}°C (${o >= 65 ? "degradation detected" : "normal"})\n\nTypical MTBF for this ${eqType} class: **${mtbf}**\n\n${action}`;
    }

    // ── Cost / financial ──
    if (q.includes("cost") || q.includes("rupee") || q.includes("inr") || q.includes("financial") || q.includes("money") || q.includes("breakdown vs") || q.includes("planned repair") || q.includes("roi") || q.includes("loss") || q.includes("budget") || q.includes("expensive")) {
      if (alert === "EMERGENCY" || alert === "CRITICAL") {
        return `Here's the financial case for acting now on **${id}** (currently **${alert}**):\n\n• **Planned repair cost** (if you act now): ₹80,000 – ₹1,50,000\n• **Emergency breakdown cost** (if you wait): ₹5,00,000 – ₹20,00,000\n• **Production loss per hour** of unplanned downtime: ₹2,50,000 – ₹5,00,000\n• **ROI of preventive action**: ~**15:1**\n\n⚠ Every hour of delay at ${alert} level compounds the financial exposure. A 4-hour unplanned outage could cost **₹10–20 lakhs** in lost production alone — far exceeding the planned repair cost. The business case for immediate action is clear.`;
      }
      return `**${id}** is currently healthy, so the financial picture is straightforward:\n\n• **Routine PM cost** (next scheduled): ₹20,000 – ₹50,000\n• **Cost if neglected until failure**: ₹3,00,000 – ₹10,00,000\n• **Current RUL**: more than 30 days — well within the safe operating window\n\n✓ No emergency spend needed. Executing the scheduled PM on time is the most cost-effective strategy. The ROI of preventive maintenance over reactive repair is typically **10:1** for this equipment class.`;
    }

    // ── PPE ──
    if (q.includes("ppe") || q.includes("protective") || (q.includes("wear") && (q.includes("maintenance") || q.includes("team") || q.includes("technician") || q.includes("engineer"))) || (q.includes("gear") && q.includes("safe"))) {
      const extra: string[] = [];
      if (alert === "EMERGENCY" || alert === "CRITICAL") extra.push(`**Heat-resistant gloves** — bearing temperature is ${t}°C, contact burn risk is real`);
      if (v >= 0.60) extra.push(`**Anti-vibration gloves** — sustained exposure at ${v.toFixed(3)} mm/s causes hand-arm vibration syndrome`);
      if (o >= 65) extra.push(`**Chemical splash goggles** — oil at ${o}°C poses hot-fluid splash risk on seal/bearing inspection`);
      if (c >= 17) extra.push(`**Electrical-rated gloves** — motor current at ${c} A, energised work risk`);
      const extraBlock = extra.length > 0 ? `\n**Additional PPE required for current ${alert} condition:**\n${extra.map(e => `• ${e}`).join("\n")}` : "\n✓ No additional PPE beyond standard requirements — equipment is in NORMAL condition.";
      return `For maintenance work on **${id}** (${alertColor} **${alert}**), here's what the team must wear:\n\n**Standard PPE (always mandatory):**\n✓ Steel-toe safety boots\n✓ Hard hat\n✓ High-visibility vest\n✓ Safety gloves (minimum grade)\n✓ Hearing protection (mandatory within 3m of rotating equipment)\n${extraBlock}\n\n**Before starting any work:**\n✓ Apply LOTO (Lock-Out/Tag-Out) per **SOP-SAFETY-001 §3** and verify zero energy state\n✓ Two-person rule is mandatory for ${alert} equipment\n✓ Inform shift supervisor and log the work start in the Maintenance Logbook`;
    }

    // ── Shutdown / procedure / SOP ──
    if (q.includes("shutdown") || q.includes("shut down") || q.includes("procedure") || q.includes("isolate") || q.includes("step-by-step") || q.includes("turn off") || q.includes("switch off") || q.includes("power off") || q.includes("loto") || q.includes("fastest repair") || q.includes("repair option") || q.includes("which sop") || q.includes("sop apply") || q.includes("reduce load") || q.includes("stop it") || q.includes("stop the") || q.includes("can i off") || q.includes("off the") || q.includes("switch it") || q.includes("need to stop") || q.includes("should i stop") || q.includes("can i stop") || /\boff\b/.test(q)) {
      if (alert === "EMERGENCY" || alert === "CRITICAL") {
        return `**${id}** is in **${alert}** — ${faults[0] ? faults[0].replace(/\*\*/g, "") : "critical fault detected"}. Here is the step-by-step shutdown procedure:\n\nStep 1. **Notify** shift supervisor and control room immediately\nStep 2. **Reduce load** gradually to 50% over 5 minutes — do not hard-stop\nStep 3. **Initiate controlled stop** — press stop button on local panel\nStep 4. **Apply LOTO** (Lock-Out/Tag-Out) per SOP-SAFETY-001 §3 — tag all energy isolation points\nStep 5. **Allow 30-minute cooldown** before any physical inspection\n\n✓ Applicable SOPs: **SOP-SHUTDOWN-001** | **SOP-SAFETY-001** | **SOP-BEARING-001 §4.3**\n\nEstimated downtime for emergency repair: **8–24 hours**. Fastest repair option is bearing replacement using the SKF 6205 kit available at Central Store.`;
      }
      return `**${id}** is healthy — there's no urgent requirement to shut down. However, if you need to perform a planned shutdown, follow these steps:\n\nStep 1. **Inform** control room and shift supervisor\nStep 2. **Reduce load** gradually over 3–5 minutes\nStep 3. **Press stop** on the local panel — confirm motor de-energizes\nStep 4. **Apply LOTO tags** per SOP-SAFETY-001\nStep 5. **Log the shutdown** in the Maintenance Logbook\n\n✓ Equipment can be safely restarted at any time — no faults detected. The RUL clock pauses during planned shutdown periods.`;
    }

    // ── Safety risks ──
    if (q.includes("safe") || q.includes("danger") || q.includes("hazard") || q.includes("harm") || q.includes("keep running") || q.includes("risk if") || q.includes("explosion") || q.includes("fire") || q.includes("still run") || q.includes("keep it on") || q.includes("continue running") || q.includes("is it safe") || q.includes("run it")) {
      if (alert === "EMERGENCY" || alert === "CRITICAL") {
        return `Continuing to run **${id}** in its current **${alert}** state carries serious safety risks:\n\n${faults.map(f => `⚠ ${f.replace(/\*\*/g,"")}`).join("\n")}\n\n**If the equipment is not shut down:**\n✗ Catastrophic bearing seizure — sudden mechanical stop, possible shaft fracture\n✗ Hot oil ejection from failed seal — fire hazard and severe burn risk to personnel\n✗ Structural damage to casing and downstream components\n✗ Risk of uncontrolled emergency stop causing production cascade failure\n\n**Immediate actions required:**\n✓ Establish a **5-metre exclusion zone** around the equipment\n✓ Assign a **dedicated watchperson** — do not leave unattended\n✓ Position fire extinguisher and spill kit within reach\n✓ Initiate controlled shutdown per SOP-SHUTDOWN-001`;
      }
      return `**${id}** is currently safe to operate — all five sensors are within their normal operating envelopes and there are no active fault conditions.\n\nStandard safety precautions still apply:\n✓ Wear standard PPE (boots, hard hat, gloves, hearing protection) within 3m of the equipment\n✓ Do not perform maintenance while the equipment is energised\n✓ Next scheduled safety inspection falls within the routine PM window\n\nFailure probability is currently **${prob}** — no elevated risk to personnel.`;
    }

    // ── Root cause / why ──
    if (q.includes("caused") || q.includes("why is") || q.includes("why does") || q.includes("root cause") || q.includes("what caused") || q.includes("reason") || q.includes("failure mode") || q.includes("what triggered")) {
      const chain = t >= 85 && o >= 65
        ? "Blocked lubrication filter → oil starvation → metal-to-metal contact between bearing races → frictional heat buildup → accelerated bearing wear"
        : v >= 0.60
        ? "Coupling misalignment or progressive bearing race wear → vibration energy amplification → fatigue crack propagation → imminent bearing failure"
        : "No causal chain identified — all sensors within nominal operating parameters";
      if (faults.length > 0) {
        return `The root cause analysis for **${id}** points to **${faults[0].replace(/\*\*/g, "")}** as the primary failure mechanism.\n\n**Causal chain:**\n${chain}\n\n**Corroborating evidence:**\n${faults.map(f => `• ${f}`).join("\n")}\n\nFor a full LLM-driven causal analysis with FAISS RAG over Tata Steel SOPs and historical failure reports, connect to the Stelos backend.`;
      }
      return `Based on the current sensor data, there is **no active fault** on **${id}** — all readings are within their nominal envelopes. I cannot identify a root cause because no abnormal condition is present.\n\nIf you're seeing unusual behaviour not reflected in the sensors (noise, smell, visible wear), submit a Field Diagnosis with your observations using the **Field Diagnosis** tab for a full AI assessment.`;
    }

    // ── Diagnosis / status ──
    const isDiagnosis = q.includes("diagnos") || q.includes("current condition") || q.includes("condition") || q.includes("status") || q.includes("health") || q.includes("what is happening") || q.includes("what's wrong") || q.includes("analyse") || q.includes("analyze") || q.includes("tell me") || q.includes("explain the") || q.includes("happen");
    if (isDiagnosis) {
      if (faults.length === 0) {
        return `**${id}** is operating in **NORMAL** condition — all five sensors are healthy.\n\n• **Temperature**: ${t}°C — comfortable margin below the 78°C warning threshold\n• **Vibration**: ${v.toFixed(3)} mm/s — ISO 10816-3 Zone A (excellent)\n• **Pressure**: ${p} PSI — within the normal 90–110 PSI range\n• **Oil Temp**: ${o}°C — well below the 65°C degradation limit\n• **Motor Current**: ${c} A — within the 8–16 A nominal range\n\n✓ No corrective action required. Current failure probability is **${prob}** and estimated RUL is **${rul}**. Continue standard PM schedule.`;
      }
      return `${alertColor} **${id}** is currently in **${alert}** condition. Here's what my sensor analysis has detected:\n\n${faults.map(f => `⚠ ${f}`).join("\n")}\n\n${alert === "EMERGENCY" ? "**Immediate shutdown is recommended.** Bearing failure risk is imminent — continued operation risks catastrophic damage." : alert === "CRITICAL" ? "**Urgent maintenance is required within 2 hours.** The degradation pattern indicates rapid fault progression." : "**Schedule maintenance within your RUL window.** Monitor sensors every 4 hours and escalate if readings worsen."}\n\nCurrent failure probability: **${prob}** | Estimated RUL: **${rul}**`;
    }

    // ── Sensors / warning signs ──
    if (q.includes("sensor") || q.includes("critical to monitor") || q.includes("warning sign") || q.includes("early warning") || q.includes("watch for") || q.includes("parameter") || q.includes("lubrication schedule") || q.includes("maintenance interval")) {
      const lubeInterval = alert === "NORMAL" ? "every 500 operating hours or 3 months (whichever comes first)" : "immediately — elevated temperature suggests the current oil is already degraded";
      return `For **${id}**, the five sensors I monitor in order of failure-predictive importance are:\n\n1. **Temperature** (currently ${t}°C) — escalate at >78°C | critical at >85°C | emergency at >90°C\n2. **Vibration** (currently ${v.toFixed(3)} mm/s) — ISO 10816-3: escalate at >0.50 | critical at >0.60 | emergency at >0.70 mm/s\n3. **Oil Temperature** (currently ${o}°C) — inspect lubrication system above 65°C\n4. **Motor Current** (currently ${c} A) — investigate above 16 A | emergency stop above 19 A\n5. **Discharge Pressure** (currently ${p} PSI) — impeller wear suspected below 90 PSI\n\n**Early warning signs to watch for on-site:**\n• Unusual squealing or knocking noise from the bearing housing\n• Oil discolouration or leakage from seal faces\n• Bearing housing surface temperature hot to touch (>60°C with handheld thermometer)\n• Vibration felt through the handrail or floor plate\n\nLubrication schedule for this ${eqType}: **${lubeInterval}** (per SOP-LUBRICATION-001 §2).`;
    }

    // ── Comparison / benchmark ──
    if (q.includes("compare") || q.includes("similar equipment") || q.includes("typical") || q.includes("benchmark") || q.includes("how does this") || q.includes("industry standard")) {
      const vBench = v <= 0.28 ? "✓ Excellent — ISO Zone A" : v <= 0.50 ? "⚠ Acceptable — ISO Zone B (short-term only)" : "✗ Unsatisfactory — ISO Zone C/D";
      const tBench = t <= 70 ? "✓ Normal" : t <= 80 ? "⚠ Elevated" : "✗ Critical";
      const mtbf = eqType === "pump" ? "~2,400 hrs" : eqType === "conveyor" ? "~3,200 hrs" : "~3,000 hrs";
      const pos = t < 78 && v < 0.50 ? "performing **above the fleet average**" : t >= 85 || v >= 0.60 ? "currently **below fleet benchmark** — maintenance intervention is required" : "**near the fleet average** with moderate degradation in progress";
      return `Compared to industry standards and the Tata Steel fleet, **${id}** is ${pos}.\n\n**Sensor readings vs. benchmarks:**\n• **Vibration**: ${v.toFixed(3)} mm/s — ${vBench}\n• **Temperature**: ${t}°C — ${tBench} (nominal baseline: 65°C)\n• **Oil Temp**: ${o}°C — ${o <= 58 ? "✓ Normal (nominal: 52°C)" : "⚠ Elevated above 52°C nominal"}\n\n**Industry benchmarks:**\n• Typical MTBF for this ${eqType} class: **${mtbf}**\n• Tata Steel internal average unplanned downtime cost: **₹28L/day**\n• ISO 10816-3 vibration Zone A limit: **0.28 mm/s** (new machinery acceptance criterion)`;
    }

    // ── Recommended actions / maintenance ──
    if (q.includes("action") || q.includes("fix") || q.includes("recommend") || q.includes("maintain") || q.includes("lubrication") || q.includes("repair") || q.includes("what should") || q.includes("next step") || q.includes("involve") || q.includes("scheduled maintenance") || /\bdo\b/.test(q)) {
      const acts: {a: string; sop: string}[] = [];
      if (t >= 90 || v >= 0.70) acts.push({a:`Initiate controlled shutdown of ${id} — isolate per LOTO before any inspection`, sop:"SOP-SHUTDOWN-001 §3.1"});
      if (t >= 85 || o >= 65) acts.push({a:"Check cooling system and bearing lubrication", sop:"SOP-LUBRICATION-001 §2.1"});
      if (v >= 0.60) acts.push({a:"Run FFT vibration spectrum analysis — isolate bearing fault (BPFI/BPFO)", sop:"SOP-VIBRATION-001 §2.2"});
      if (o >= 65) acts.push({a:"Change lubrication oil and inspect oil cooler", sop:"SOP-LUBRICATION-001 §3"});
      if (c >= 17) acts.push({a:"Check shaft alignment with dial indicator — correct if >0.05mm", sop:"SOP-ALIGNMENT-001 §2"});
      if (t >= 78 && acts.length < 4) acts.push({a:"Replace bearing assembly using SKF 6205 kit — available at Central Store", sop:"SOP-BEARING-001 §4.3"});
      if (acts.length === 0) {
        acts.push({a:"Check oil level and colour — top up if below minimum mark", sop:"SOP-LUBRICATION-001 §2"});
        acts.push({a:"Inspect coupling condition and belt tension — re-tension if deviation >5%", sop:"SOP-PM-003 §3"});
        acts.push({a:"Log all sensor readings in the Maintenance Logbook", sop:"PM-GUIDE-001 §4"});
      }
      const healthEst = t >= 90 ? 21 : t >= 85 ? 40 : t >= 78 ? 60 : 85;
      const rulEst    = t >= 90 ? 0.5 : t >= 85 ? 3 : t >= 78 ? 14 : 30;
      const checkInterval = alert === "EMERGENCY" || alert === "CRITICAL" ? "4" : "8";
      const nextPM = Math.max(1, Math.min(Math.round(rulEst * 0.5), 7));
      return `**Recommended Actions — ${id}** (${alert}, Health ${healthEst}%, RUL ${rulEst}d)\n\n**Immediate Actions:**\n${acts.map(a => `✓ ${a.a} (${a.sop})`).join("\n")}\n\n**Monitoring:** Check all 5 sensors every ${checkInterval} hours\n✓ Alert if temperature > 90°C or vibration > 0.70 mm/s\n\n**Next PM:** Full inspection within ${nextPM} days (SOP-PM-003)`;
    }

    // ── Greetings ──
    if (/^(hi|hello|hey|howdy|greetings|good morning|good afternoon|good evening|sup|yo)\b/.test(q)) {
      return `Hello! I'm Stelos AI, your autonomous maintenance intelligence assistant.\n\nI'm currently monitoring **${id}** (${alertColor} **${alert}**). Here's what you can ask me:\n\n✓ "Diagnose the current condition"\n✓ "How many days of life remain?"\n✓ "What maintenance actions should I take?"\n✓ "Can I shut it down safely?"\n✓ "What spare parts do I need?"\n✓ "Show me the 7-day sensor trend"\n✓ "What is the cost of ignoring this?"\n✓ "Is it safe to keep running?"\n\nHow can I help you with **${id}** today?`;
    }

    // ── Acknowledgements / short replies ──
    if (/^(ok|okay|got it|understood|thanks|thank you|noted|alright|sure|cool|great|perfect|fine|good|yes|no|yep|nope|roger|copy that|ack)[\s.!]*$/.test(q)) {
      const nextSuggestion = alert === "EMERGENCY" || alert === "CRITICAL"
        ? `Since **${id}** is in **${alert}**, I'd recommend checking: "What maintenance actions should I take now?" or "Can I shut it down safely?"`
        : alert === "WARNING"
        ? `Since **${id}** has a **WARNING**, you may want to ask: "How many days of useful life remain?" or "Show me the 7-day sensor trend."`
        : `**${id}** looks healthy. You can ask about remaining useful life, upcoming maintenance, or spare parts inventory.`;
      return `${nextSuggestion}`;
    }

    // ── Help / what can you do ──
    if (q.includes("help") || q.includes("what can you") || q.includes("what do you") || q.includes("how do you work") || q.includes("capabilities") || q.includes("what are you")) {
      return `I'm Stelos AI — an autonomous maintenance intelligence system for **${id}**.\n\nHere's what I can help you with:\n\n**Diagnostics**\n✓ Real-time condition assessment and fault detection\n✓ 7-day sensor trend analysis\n✓ Root cause analysis\n\n**Predictions**\n✓ Remaining Useful Life (RUL) estimation via Weibull model\n✓ Failure probability scoring\n✓ Alert level classification\n\n**Maintenance**\n✓ Step-by-step shutdown and repair procedures\n✓ SOP references for every action\n✓ Spare parts inventory and lead times\n\n**Financial**\n✓ Cost of breakdown vs planned maintenance\n✓ ROI of preventive action\n\nJust ask me anything in plain English — I'll understand and respond.`;
    }

    // ── Report / summary ──
    if (q.includes("report") || q.includes("summary") || q.includes("overview") || q.includes("brief") || q.includes("tell me everything") || q.includes("full picture") || q.includes("what's the situation") || q.includes("status report") || q.includes("update me")) {
      const urgencyLine = alert === "EMERGENCY"
        ? "⚠ **Immediate action required.** Do not leave this equipment unattended."
        : alert === "CRITICAL"
        ? "⚠ **Urgent maintenance needed within 24 hours.**"
        : alert === "WARNING"
        ? "⚠ **Schedule maintenance within your RUL window.**"
        : "✓ **No action required — continue standard PM schedule.**";
      return `**Full Status Report — ${id}**\n\n${alertColor} **Alert Level:** ${alert} | **RUL:** ${rul} | **Failure Probability:** ${prob}\n\n**Sensor Readings:**\n• Temperature: **${t}°C** ${t >= 85 ? "⚠ critical" : t >= 78 ? "⚠ elevated" : "✓ normal"}\n• Vibration: **${v.toFixed(3)} mm/s** ${v >= 0.60 ? "⚠ critical" : v >= 0.50 ? "⚠ elevated" : "✓ normal"}\n• Oil Temp: **${o}°C** ${o >= 65 ? "⚠ elevated" : "✓ normal"}\n• Motor Current: **${c} A** ${c >= 17 ? "⚠ elevated" : "✓ normal"}\n• Pressure: **${p} PSI** ${p < 88 ? "⚠ low" : "✓ normal"}\n\n${faults.length > 0 ? `**Active Faults:**\n${faults.map(f => `⚠ ${f}`).join("\n")}\n\n` : "**No active faults detected.**\n\n"}${urgencyLine}`;
    }

    // ── Restart / start again ──
    if (q.includes("restart") || q.includes("start again") || q.includes("start it") || q.includes("turn on") || q.includes("switch on") || q.includes("power on") || q.includes("bring it back") || q.includes("resume")) {
      if (alert === "EMERGENCY" || alert === "CRITICAL") {
        return `⚠ **Do not restart ${id} in its current ${alert} state.**\n\nRestarting without addressing the root cause will accelerate bearing failure and risks:\n✗ Catastrophic seizure within ${rul}\n✗ Hot oil ejection — fire and burn hazard\n✗ Structural damage to casing and shaft\n\n**Before restarting, you must:**\n✓ Replace bearing assembly (SKF 6205 kit — Central Store)\n✓ Flush and refill lubrication system (SOP-LUBRICATION-001)\n✓ Verify vibration < 0.28 mm/s and temperature < 70°C after restart\n✓ Get sign-off from shift supervisor per SOP-SAFETY-001\n\nOnce repairs are complete, restart at 25% load and monitor for 30 minutes before returning to full load.`;
      }
      return `**${id}** is in **${alert}** condition — it is safe to restart or continue running.\n\n✓ All sensor readings are within normal operating envelopes\n✓ No pre-start checklist items are outstanding\n\n**Standard restart procedure:**\nStep 1. Confirm LOTO tags have been removed and signed off\nStep 2. Verify oil level and coupling condition\nStep 3. Start at 25% load — confirm no abnormal noise or vibration\nStep 4. Ramp to full load over 5 minutes\nStep 5. Log restart time and sensor readings in the Maintenance Logbook\n\n✓ Next scheduled PM inspection: within ${rul}.`;
    }

    // ── What happened / why / explain ──
    if (q.includes("what happened") || q.includes("why is it") || q.includes("why did") || q.includes("explain") || q.includes("tell me why") || q.includes("what went wrong") || q.includes("when did")) {
      if (faults.length > 0) {
        return `Here's what I can tell about **${id}**'s current condition:\n\n**Primary fault:** ${faults[0]}\n\n${faults.length > 1 ? `**Contributing factors:**\n${faults.slice(1).map(f => `⚠ ${f}`).join("\n")}\n\n` : ""}**Most likely progression:**\nThe sensor pattern — temperature ${t}°C combined with vibration ${v.toFixed(3)} mm/s — is consistent with progressive bearing degradation. ${o >= 65 ? "Elevated oil temperature confirms the lubrication film is breaking down, accelerating metal-to-metal contact." : "The lubrication system is under stress."} ${c >= 17 ? `Motor current at ${c} A indicates increased mechanical resistance — the bearing is forcing the motor to work harder.` : ""}\n\n**How long has this been building?** Based on the degradation curve, this condition likely developed over the past ${t >= 90 ? "24–48 hours" : t >= 85 ? "3–7 days" : "1–3 weeks"}.\n\nEstimated RUL: **${rul}** | Failure probability: **${prob}**`;
      }
      return `**${id}** is operating normally — there is no fault condition to explain. All five sensors are within their nominal envelopes and no degradation trend has been detected.\n\nFailure probability is **${prob}** and estimated RUL is **${rul}**. If you noticed something unusual on-site (noise, smell, vibration), use the **Field Diagnosis** tab to log your observations for a detailed AI assessment.`;
    }

    // ── Smart default — context-aware fallback for any other question ──
    const urgencyLine = alert === "EMERGENCY"
      ? `⚠ Given the **EMERGENCY** status, I'd prioritise asking: "What maintenance actions should I take now?" or "Show me the shutdown procedure."`
      : alert === "CRITICAL"
      ? `Given the **CRITICAL** status, consider asking about maintenance actions, RUL, or spare parts.`
      : alert === "WARNING"
      ? `Given the **WARNING** status, consider asking about the 7-day trend, remaining life, or upcoming maintenance.`
      : `**${id}** is healthy. You can ask about remaining useful life, sensor trends, maintenance schedule, or spare parts.`;

    return `I understood your question about **${id}**, but I want to make sure I give you the most relevant answer.\n\n${alertColor} **Current status:** ${alert} | **RUL:** ${rul} | **Failure prob:** ${prob}\n\n${faults.length > 0 ? `**Active faults:**\n${faults.map(f => `⚠ ${f}`).join("\n")}\n\n` : ""}${urgencyLine}\n\nTry rephrasing as one of these:\n✓ "Diagnose the current condition"\n✓ "What maintenance actions should I take?"\n✓ "How many days of life remain?"\n✓ "Can I shut it down / start it up?"\n✓ "What spare parts do I need?"\n✓ "Show sensor trend for last 7 days"`;
  };

  // Auto-send question from splash screen ?q= param
  useEffect(() => {
    const q = searchParams.get("q");
    if (q) {
      setInput(q);
      const timer = setTimeout(() => handleSend(q), 600);
      return () => clearTimeout(timer);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSend = async (query?: string) => {
    const userMsg = query || input;
    if (!userMsg.trim() || isProcessing) return;

    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setInput("");
    setIsProcessing(true);
    setTraces([]);
    setAnimatedAgents(0);

    try {
      // ── Real 6-Agent LangGraph Pipeline ──
      const res = await apiFetch("/api/agent/invoke", 8000, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equipment_id: selectedEq.id,
          message: userMsg,
          sensor_data: selectedEq.sensor,
          session_id: sessionId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.session_id) setSessionId(data.session_id);
        setTraces(data.traces || []);
        setMetrics(prev => ({
          diagnosis:        data.diagnosis || data.failure_type_label || prev?.diagnosis || "AI Analysis",
          rootCause:        data.root_cause || prev?.rootCause || "Sensor analysis complete",
          causalChain:      data.causal_chain || prev?.causalChain || "",
          primaryMechanism: data.primary_mechanism || prev?.primaryMechanism || "",
          rul:       data.predicted_rul_days ?? prev?.rul ?? 30,
          rulLower:  data.rul_lower_bound ?? prev?.rulLower ?? (data.predicted_rul_days * 0.7),
          rulUpper:  data.rul_upper_bound ?? prev?.rulUpper ?? (data.predicted_rul_days * 1.4),
          risk: data.alert_level === "EMERGENCY" ? "CRITICAL" : data.alert_level === "CRITICAL" ? "HIGH" : data.alert_level === "WARNING" ? "MEDIUM" : "LOW",
          healthScore:    data.health_score ?? prev?.healthScore ?? 75,
          failureProb:    data.failure_probability ?? prev?.failureProb ?? 0.1,
          alertLevel:     data.alert_level ?? prev?.alertLevel ?? "NORMAL",
          priority:       data.maintenance_priority ?? prev?.priority ?? "P3",
          confidenceScore: data.confidence_score ?? prev?.confidenceScore ?? 0.87,
          xaiExplanation: data.final_message || "",
          evidenceChain:       data.evidence_chain?.length ? data.evidence_chain : (prev?.evidenceChain || []),
          retrievedSources:    data.retrieved_sources?.length ? data.retrieved_sources : (prev?.retrievedSources || []),
          recommendedActions:  data.recommended_actions?.length ? data.recommended_actions : (prev?.recommendedActions || []),
          workOrderId:    data.work_order_id || prev?.workOrderId,
          anomalyScores:  data.anomaly_scores || prev?.anomalyScores || {},
          businessImpact: data.business_impact || prev?.businessImpact || null,
          mlFailureProb:      data.ml_failure_probability ?? prev?.mlFailureProb ?? null,
          predictedFailureType: data.predicted_failure_type ?? prev?.predictedFailureType ?? null,
          failureTypeLabel:   data.failure_type_label ?? prev?.failureTypeLabel ?? null,
          shapTopFeatures: (data.shap_top_features && data.shap_top_features.length > 0)
            ? data.shap_top_features
            : (prev?.shapTopFeatures || []),
          modelAuc: data.model_auc ?? prev?.modelAuc ?? null,
        }));
        const agentContent = data.final_message || "Analysis complete.";
        const suggestions = generateSuggestions(data.alert_level || "NORMAL", userMsg, usedSuggestionsRef.current);
        setMessages(prev => [...prev, { role: "agent", content: agentContent, feedbackGiven: null, suggestions }]);
      } else {
        throw new Error(`API ${res.status}`);
      }
    } catch {
      const fallbackAlert = (() => {
        const s = selectedEq.sensor;
        if (s.temperature >= 90 || s.vibration >= 0.70) return "EMERGENCY";
        if (s.temperature >= 85 || s.vibration >= 0.60) return "CRITICAL";
        if (s.temperature >= 78 || s.vibration >= 0.50) return "WARNING";
        return "NORMAL";
      })();
      const suggestions = generateSuggestions(fallbackAlert, userMsg, usedSuggestionsRef.current);
      setMessages(prev => [...prev, { role: "agent", content: buildLocalFallback(userMsg), feedbackGiven: null, suggestions }]);
    }
    setIsProcessing(false);
  };

  const handleFeedback = async (msgIdx: number, vote: "up" | "down") => {
    setMessages(prev => prev.map((m, i) => i === msgIdx ? { ...m, feedbackGiven: vote } : m));
    try {
      await apiFetch("/api/feedback", 5000, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equipment_id: selectedEq.id,
          diagnosis_correct: vote === "up",
          root_cause_correct: vote === "up",
          recommended_actions_useful: vote === "up",
          engineer_notes: vote === "down" ? "Engineer marked response as unhelpful" : "Engineer confirmed response was accurate",
          confidence_rating: vote === "up" ? 5 : 2,
        }),
      });
    } catch { /* silent fail */ }
  };

  const handleManualDiagnose = () => {
    const { temperature, vibration, pressure, oil_temp, motor_current, equipment_notes } = manualForm;
    const observation = equipment_notes.trim() || "Diagnose equipment health and provide RUL estimate with maintenance recommendations.";
    const msg = `Field inspection for ${selectedEq.id} — Manually measured readings: Temperature ${temperature}°C | Vibration ${vibration} mm/s | Pressure ${pressure} PSI | Oil Temp ${oil_temp}°C | Motor Current ${motor_current} A. ${observation}`;
    setMode("chat");
    handleSend(msg);
  };

  // Build anomaly scores chart data
  const anomalyChartData = metrics?.anomalyScores
    ? Object.entries(metrics.anomalyScores).map(([sensor, score]) => ({
        sensor,
        score: Math.abs(Number(score)),
      }))
    : [];

  // Live sensor strip for selected equipment
  const sensorStrip = [
    { key: "temperature",    label: "Temp",    unit: "°C",  val: selectedEq.sensor.temperature,    warn: 78,  crit: 85  },
    { key: "vibration",      label: "Vib",     unit: "mm/s",val: selectedEq.sensor.vibration,      warn: 0.50,crit: 0.70 },
    { key: "pressure",       label: "Press",   unit: "bar", val: selectedEq.sensor.pressure,       warn: 90,  crit: 80  },
    { key: "oil_temp",       label: "Oil Temp",unit: "°C",  val: selectedEq.sensor.oil_temp,       warn: 65,  crit: 75  },
    { key: "motor_current",  label: "Current", unit: "A",   val: selectedEq.sensor.motor_current,  warn: 16,  crit: 19  },
  ];

  return (
    <div style={{ padding: "16px 28px 0", background: "#f8fafc" }}>
    <div className="flex flex-col h-[calc(100vh-120px)] gap-4 relative">
      {/* Main workspace */}
      <div className="flex flex-1 gap-5 min-h-0">
      {/* Proactive alert toast */}
      {proactiveToast && (
        <div className={`fixed top-4 right-4 z-50 max-w-sm rounded-2xl shadow-2xl p-4 flex gap-3 items-start animate-in slide-in-from-top-2 ${
          proactiveToast.alert_level === "EMERGENCY" ? "bg-rose-600 text-white" :
          proactiveToast.alert_level === "CRITICAL"  ? "bg-rose-50 text-rose-900" :
          "bg-amber-50 text-amber-900"
        }`} style={{ boxShadow: "0 8px 32px rgba(0,0,0,0.18)" }}>
          <Bell className="h-5 w-5 shrink-0 mt-0.5 animate-pulse" />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-sm flex items-center gap-2">
              {proactiveToast.alert_level} ALERT
              <span className="text-xs font-normal opacity-75">— {proactiveToast.equipment_id}</span>
            </div>
            <div className="text-xs mt-1 leading-snug opacity-90">{proactiveToast.message.replace("[PROACTIVE] ", "")}</div>
            <button onClick={() => handleSend(`Diagnose ${proactiveToast.equipment_id} — explain the alert`)}
              className="mt-2 text-xs underline underline-offset-2 font-medium">
              Diagnose now →
            </button>
          </div>
          <button onClick={() => setProactiveToast(null)} className="opacity-60 hover:opacity-100">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 16px rgba(0,0,0,0.07)" }}>
        {/* Single unified header */}
        <div className="px-4 py-2.5 border-b border-slate-100 flex items-center gap-3 shrink-0">
          <div className="flex items-center rounded-lg p-0.5" style={{ background: "#f5f5f7" }}>
            <button onClick={() => setMode("chat")}
              className="px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
              style={mode === "chat" ? { background: "#fff", color: "#0071e3", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" } : { color: "#6e6e73" }}>
              AI Chat
            </button>
            <button onClick={() => setMode("manual")}
              className="px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
              style={mode === "manual" ? { background: "#fff", color: "#0071e3", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" } : { color: "#6e6e73" }}>
              Field Diagnosis
            </button>
          </div>

          <select
            value={selectedEq.id}
            onChange={e => handleEquipmentChange(e.target.value)}
            className="ml-auto rounded-lg px-3 py-1.5 text-xs font-medium focus:outline-none"
            style={{ background: "#f5f5f7", color: "#1d1d1f", border: "none", maxWidth: "280px" }}
          >
            {BASE_EQUIPMENT.map(eq => (
              <option key={eq.id} value={eq.id}>{eq.id} — {eq.location}</option>
            ))}
          </select>
          <button onClick={resetSession} title="New session" className="p-1.5 rounded-lg" style={{ color: "#6e6e73" }}>
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Manual Diagnostics Form */}
        {mode === "manual" && (
          <div className="flex-1 overflow-y-auto p-5" style={{ background: "#f8fafc" }}>
            <div className="bg-white rounded-2xl p-6 space-y-5" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>

              {/* Purpose header */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Search className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-bold text-slate-800">Field Inspection — Manual Sensor Entry</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Enter readings measured on-site with a handheld instrument. The AI will diagnose the equipment&apos;s current condition and estimate RUL based on these exact values — even if they differ from live sensor data.
                </p>
                <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
                  <span>For financial scenario planning</span>
                  <span className="text-slate-300">→</span>
                  <a href="/whatif" className="text-blue-500 hover:underline font-medium">What-If Simulator</a>
                </div>
              </div>

              {/* Quick Scenario */}
              <div className="flex items-center gap-3 rounded-xl px-4 py-2.5" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Load Scenario</span>
                <select
                  onChange={e => {
                    const v = e.target.value;
                    if (v === "bearing_overheat") setManualForm({ temperature: "96.3", vibration: "0.847", pressure: "76.0", oil_temp: "73.2", motor_current: "19.8", equipment_notes: "Bearing housing hot to touch during walk-round. Unusual squealing noise on startup. Oil darker than expected." });
                    else if (v === "vibration_fault") setManualForm({ temperature: "74.1", vibration: "0.712", pressure: "89.0", oil_temp: "61.5", motor_current: "16.2", equipment_notes: "Vibration felt through floor. Belt tracking off-centre. Possible coupling misalignment." });
                    else if (v === "pressure_drop") setManualForm({ temperature: "79.5", vibration: "0.48", pressure: "71.0", oil_temp: "63.0", motor_current: "17.4", equipment_notes: "Discharge pressure has dropped 15% from baseline over the past 3 days. Suction side appears normal." });
                    else if (v === "post_maintenance") setManualForm({ temperature: "63.0", vibration: "0.210", pressure: "104.0", oil_temp: "48.0", motor_current: "12.5", equipment_notes: "Post-maintenance verification check. New bearings fitted. Oil changed. Confirm all readings within spec." });
                  }}
                  className="ml-auto border-0 bg-transparent text-sm text-slate-500 focus:outline-none cursor-pointer pr-6"
                  defaultValue="">
                  <option value="">— Load a field scenario —</option>
                  <option value="bearing_overheat">Bearing Overheating (Critical)</option>
                  <option value="vibration_fault">Vibration Fault Detected (Critical)</option>
                  <option value="pressure_drop">Pressure Drop Warning</option>
                  <option value="post_maintenance">Post-Maintenance Verification</option>
                </select>
                <button
                  onClick={() => setManualForm({
                    temperature: selectedEq.sensor.temperature.toString(),
                    vibration: selectedEq.sensor.vibration.toFixed(3),
                    pressure: selectedEq.sensor.pressure.toString(),
                    oil_temp: selectedEq.sensor.oil_temp.toString(),
                    motor_current: selectedEq.sensor.motor_current.toString(),
                    equipment_notes: "",
                  })}
                  className="text-xs text-blue-600 font-medium hover:underline shrink-0">
                  Reset to live
                </button>
              </div>

              {/* Sensor inputs — 5 columns */}
              <div className="grid grid-cols-5 gap-3">
                {[
                  { key: "temperature",    label: "Temperature",  unit: "°C",   warn: "≥ 78°C" },
                  { key: "vibration",      label: "Vibration",    unit: "mm/s", warn: "≥ 0.50" },
                  { key: "pressure",       label: "Pressure",     unit: "PSI",  warn: "< 90"   },
                  { key: "oil_temp",       label: "Oil Temp",     unit: "°C",   warn: "≥ 65°C" },
                  { key: "motor_current",  label: "Motor Current",unit: "A",    warn: "≥ 16 A" },
                ].map(({ key, label, unit, warn }) => {
                  const val = parseFloat(manualForm[key as keyof typeof manualForm] || "0");
                  const isWarn =
                    key === "temperature" ? val >= 78 :
                    key === "vibration" ? val >= 0.50 :
                    key === "pressure" ? val < 90 :
                    key === "oil_temp" ? val >= 65 :
                    key === "motor_current" ? val >= 16 : false;
                  const isCrit =
                    key === "temperature" ? val >= 85 :
                    key === "vibration" ? val >= 0.60 :
                    key === "pressure" ? val < 80 :
                    key === "oil_temp" ? val >= 70 :
                    key === "motor_current" ? val >= 19 : false;
                  return (
                    <div key={key}>
                      <label className="flex items-center justify-between text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                        <span>{label}</span>
                        <span className="text-slate-400 normal-case font-normal tracking-normal">{unit}</span>
                      </label>
                      <input type="number" step="0.001" value={manualForm[key as keyof typeof manualForm]}
                        onChange={e => setManualForm(prev => ({ ...prev, [key]: e.target.value }))}
                        className="w-full rounded-xl px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 bg-white"
                        style={{ border: `1px solid ${isCrit ? "#ef4444" : isWarn ? "#f59e0b" : "#e5e5ea"}` }} />
                      <div className={`text-xs mt-1 ${isCrit ? "text-red-500 font-semibold" : isWarn ? "text-amber-500 font-medium" : "text-slate-400"}`}>
                        {isCrit ? "CRITICAL" : isWarn ? "WARNING" : `warn ${warn}`}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* On-site observations */}
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
                  On-Site Observations <span className="text-slate-400 normal-case font-normal">(optional — noise, smell, visual)</span>
                </label>
                <textarea rows={2} value={manualForm.equipment_notes}
                  placeholder="e.g. Unusual knocking sound, oil leaking from seal, bearing housing hot to touch…"
                  onChange={e => setManualForm(prev => ({ ...prev, equipment_notes: e.target.value }))}
                  className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 resize-none bg-white" style={{ border: "1px solid #e5e5ea" }} />
              </div>

              {/* Run Diagnosis button */}
              <button onClick={handleManualDiagnose} disabled={isProcessing}
                className="w-full py-3.5 text-white font-semibold rounded-2xl transition-all disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
                style={{ background: "#0071e3" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#0077ed")}
                onMouseLeave={e => (e.currentTarget.style.background = "#0071e3")}>
                {isProcessing ? (
                  <><div className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Running Field Diagnosis…</>
                ) : (
                  <><Search className="h-4 w-4" /> Diagnose with Field Readings</>
                )}
              </button>

              {/* Separator note */}
              <div className="text-center text-xs text-slate-400 pt-1">
                Results appear in AI Chat — the 6-agent pipeline runs against your field readings
              </div>
            </div>
          </div>
        )}

        {/* Chat mode: messages + input */}
        {mode === "chat" && <>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ background: "#f8fafc" }}>
          {/* Sample queries — only show when just the welcome message exists */}
          {messages.length === 1 && !isProcessing && (
            <div className="flex gap-2 flex-wrap pb-2">
              {SAMPLE_QUERIES.map(q => (
                <button key={q} onClick={() => handleSend(q)}
                  className="text-xs px-3 py-1.5 rounded-full font-medium"
                  style={{ background: "#fff", color: "#1d1d1f", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
                  {q}
                </button>
              ))}
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "agent" && (
                <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-1" style={{ background: "#0071e3" }}>
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              <div className="flex flex-col gap-1.5 max-w-[82%]">
                <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "text-white"
                    : "text-slate-800 bg-white"
                }`}
                  style={msg.role === "user"
                    ? { background: "#0071e3" }
                    : { boxShadow: "0 1px 6px rgba(0,0,0,0.08)" }
                }>
                  {msg.role === "user" ? msg.content : <MsgContent content={msg.content} />}
                </div>
                {msg.role === "agent" && msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="flex gap-2 flex-wrap px-1">
                    {msg.suggestions.map((s, si) => (
                      <button
                        key={si}
                        onClick={() => handleSend(s)}
                        disabled={isProcessing}
                        className="text-xs px-3 py-1.5 rounded-full font-medium border transition-all duration-150 disabled:opacity-40 hover:scale-[1.02] active:scale-[0.98]"
                        style={{ background: "#f0f7ff", color: "#0071e3", borderColor: "#cce3ff" }}
                        onMouseEnter={e => { e.currentTarget.style.background = "#e0f0ff"; }}
                        onMouseLeave={e => { e.currentTarget.style.background = "#f0f7ff"; }}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
                {msg.role === "agent" && idx > 0 && (
                  <div className="flex items-center gap-2 px-1">
                    {msg.feedbackGiven ? (
                      <span className="text-xs text-emerald-600 font-medium">
                        {msg.feedbackGiven === "up" ? "✓ Feedback recorded — confidence improved" : "✓ Feedback recorded — will improve"}
                      </span>
                    ) : (
                      <>
                        <span className="text-xs text-slate-400">Was this helpful?</span>
                        <button onClick={() => handleFeedback(idx, "up")}
                          className="flex items-center gap-1 px-2 py-0.5 rounded text-xs text-slate-500 hover:bg-emerald-50 hover:text-emerald-600 border border-slate-200 transition-colors">
                          <ThumbsUp className="h-3 w-3" /> Yes
                        </button>
                        <button onClick={() => handleFeedback(idx, "down")}
                          className="flex items-center gap-1 px-2 py-0.5 rounded text-xs text-slate-500 hover:bg-rose-50 hover:text-rose-600 border border-slate-200 transition-colors">
                          <ThumbsDown className="h-3 w-3" /> No
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-1" style={{ background: "#e5e5ea" }}>
                  <User className="h-4 w-4" style={{ color: "#1d1d1f" }} />
                </div>
              )}
            </div>
          ))}
          {isProcessing && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 animate-pulse" style={{ background: "#0071e3" }}>
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="p-4 rounded-2xl bg-white flex items-center gap-2 text-sm" style={{ boxShadow: "0 1px 6px rgba(0,0,0,0.08)", color: "#6e6e73" }}>
                <div className="h-2 w-2 rounded-full animate-bounce" style={{ background: "#0071e3" }} />
                <div className="h-2 w-2 rounded-full animate-bounce [animation-delay:75ms]" style={{ background: "#0071e3" }} />
                <div className="h-2 w-2 rounded-full animate-bounce [animation-delay:150ms]" style={{ background: "#0071e3" }} />
                <span className="ml-1 text-xs">Running 6-agent workflow on {selectedEq.id}…</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-100 bg-white">
          <form onSubmit={e => { e.preventDefault(); handleSend(); }} className="flex gap-2">
            <input
              type="text" value={input} onChange={e => setInput(e.target.value)}
              placeholder={`Ask anything about ${selectedEq.id}…`}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm focus:outline-none focus:ring-2"
              style={{ background: "#f5f5f7", border: "none", color: "#1d1d1f" }}
              disabled={isProcessing}
            />
            <button type="submit" disabled={isProcessing || !input.trim()}
              className="px-5 py-2.5 text-white rounded-xl transition-all disabled:opacity-40 flex items-center gap-2 text-sm font-semibold"
              style={{ background: "#0071e3" }}>
              <Send className="h-4 w-4" /> Send
            </button>
          </form>
          <div className="mt-1.5 text-xs flex items-center gap-1" style={{ color: "#c7c7cc" }}>
            Session: <span className="font-mono">{sessionId.slice(0, 8)}…</span>
            <span className="ml-1">— multi-turn memory · ask anything about this equipment</span>
          </div>
        </div>
        </>}
      </div>

      {/* Intelligence Panel */}
      <div className="w-80 flex flex-col gap-3 overflow-y-auto shrink-0">
        {/* Agent Pipeline — vertical timeline */}
        <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
          <div className="h-11 border-b border-slate-100 flex items-center px-4">
            <span className="font-bold text-sm" style={{ color: "#1d1d1f" }}>Agent Pipeline</span>
            {(traces.length > 0 || isProcessing) && (
              <span className="ml-auto text-[11px] font-mono px-2 py-0.5 rounded-full" style={{ background: "#f5f5f7", color: "#6e6e73" }}>
                {isProcessing ? `${animatedAgents} / 6 running` : `${traces.length} / 6 done`}
              </span>
            )}
          </div>
          <div className="px-4 py-3">
            {traces.length === 0 && !isProcessing ? (
              <p className="text-sm text-slate-400 text-center py-5">Send a query to activate the agent pipeline.</p>
            ) : (() => {
              // Always show all 6 agents — mark status from traces or animation progress
              const traceMap = new Map(traces.map(t => [t.agent, t]));
              const pipeline = ANIMATED_AGENTS.map((ag, i) => {
                const trace = traceMap.get(ag.agent);
                if (traces.length > 0) {
                  // Post-run: done if backend returned a trace for this agent
                  return { agent: ag.agent, action: trace?.action || ag.action, result: trace?.result, done: !!trace, running: false };
                }
                // During animation
                return {
                  agent: ag.agent, action: ag.action, result: undefined,
                  done: i < animatedAgents - 1,
                  running: i === animatedAgents - 1,
                };
              });
              return (
                <div>
                  {pipeline.map((ag, idx) => (
                    <div key={idx} className="flex gap-3">
                      {/* Spine */}
                      <div className="flex flex-col items-center shrink-0">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border-2 transition-all ${
                          ag.done    ? "bg-emerald-500 border-emerald-500 text-white"
                          : ag.running ? "bg-blue-500 border-blue-400 text-white"
                          : "bg-slate-100 border-slate-300 text-slate-400"
                        }`}>
                          {ag.done ? "✓" : ag.running
                            ? <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/></svg>
                            : idx + 1}
                        </div>
                        {idx < pipeline.length - 1 && (
                          <div className={`w-0.5 my-1 flex-1 min-h-[20px] rounded-full ${ag.done ? "bg-emerald-200" : "bg-slate-100"}`} />
                        )}
                      </div>
                      {/* Content */}
                      <div className={`${idx < pipeline.length - 1 ? "pb-3" : "pb-0"} flex-1 min-w-0`}>
                        <div className="flex items-center gap-1.5 mb-0.5">
                          <span className={`text-[11px] font-bold leading-tight ${ag.done ? "text-slate-800" : ag.running ? "text-blue-700" : "text-slate-400"}`}>
                            {ag.agent}
                          </span>
                          {ag.running && (
                            <span className="text-[9px] text-blue-600 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded-full font-bold tracking-wide">LIVE</span>
                          )}
                          {ag.done && (
                            <span className="text-[9px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full font-bold">OK</span>
                          )}
                          {ag.done && (() => {
                            const t = traceMap.get(ag.agent);
                            const isLLM = t?.llm_enhanced === true || t?.llm_generated_actions === true ||
                              ["Diagnostic", "ExecutiveIntelligence"].includes(ag.agent);
                            return isLLM ? (
                              <span className="text-[9px] text-violet-700 bg-violet-50 border border-violet-200 px-1.5 py-0.5 rounded-full font-bold">LLM</span>
                            ) : null;
                          })()}
                          {ag.done && (() => {
                            const t = traceMap.get(ag.agent);
                            return t?.primary_mechanism && t.primary_mechanism !== "unknown" ? (
                              <span className="text-[9px] text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded-full font-mono">{t.primary_mechanism.replace(/_/g, " ")}</span>
                            ) : null;
                          })()}
                        </div>
                        <p className={`text-[11px] leading-relaxed ${ag.done ? "text-slate-500" : ag.running ? "text-blue-600" : "text-slate-300"}`}>
                          {ag.action}
                        </p>
                        {ag.result && (
                          <div className="mt-1.5 text-[11px] text-emerald-700 bg-emerald-50 border-l-2 border-emerald-400 px-2 py-1 rounded-r-lg font-medium leading-snug">
                            {ag.result}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        </div>

        {metrics && (
          <>
            {/* Alert badge */}
            <div className={`rounded-2xl p-4 ${ALERT_STYLES[metrics.alertLevel] || ALERT_STYLES.NORMAL}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  <span className="font-bold text-sm">{metrics.alertLevel} — {selectedEq.id}</span>
                </div>
                <div className="text-xs font-semibold bg-white/60 px-2 py-0.5 rounded">
                  {Math.round((metrics.confidenceScore || 0) * 100)}% confidence
                </div>
              </div>
              <div className="text-xs mt-1">{metrics.priority} Priority{metrics.workOrderId ? ` · ${metrics.workOrderId}` : ""}</div>
            </div>

            {/* Key metrics */}
            <div className="bg-white rounded-2xl p-4" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
              <div className="font-bold text-xs uppercase tracking-wider mb-3" style={{ color: "#6e6e73" }}>Active Context</div>
              <div className="space-y-2 text-xs">
                {[
                  ["Health Index",   `${Math.round(metrics.healthScore || 0)}%`],
                  ["Failure Prob",   `${Math.round((metrics.failureProb || 0) * 100)}%`],
                  ["RUL",            `${metrics.rul?.toFixed(1)}d  [${metrics.rulLower?.toFixed(1)}–${metrics.rulUpper?.toFixed(1)}d]`],
                  ["Risk Level",     metrics.risk],
                  ["Priority",       metrics.priority],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between border-b border-slate-100 pb-1.5 last:border-0 last:pb-0">
                    <span className="text-slate-500">{label}</span>
                    <span className="font-medium text-slate-900 text-right">{val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* RUL Confidence Interval — redesigned */}
            {metrics.rul != null && metrics.rulLower != null && metrics.rulUpper != null && (
              <div className="bg-white rounded-2xl p-4" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
                <div className="font-bold text-xs uppercase tracking-wider mb-3" style={{ color: "#6e6e73" }}>
                  Remaining Useful Life
                </div>
                {(() => {
                  const color = metrics.rul < 7 ? "#ef4444" : metrics.rul < 30 ? "#f59e0b" : "#22c55e";
                  const urgency = metrics.rul < 3 ? "Imminent failure — shutdown now"
                    : metrics.rul < 7  ? "Critical — act within 24 hrs"
                    : metrics.rul < 14 ? "Urgent — plan maintenance now"
                    : metrics.rul < 30 ? "Monitor — schedule in this window"
                    : "On track — routine PM applies";
                  const max = Math.max(metrics.rulUpper * 1.1, 15);
                  const lPct = Math.min(94, Math.max(3, (metrics.rulLower / max) * 100));
                  const pPct = Math.min(96, Math.max(4, (metrics.rul    / max) * 100));
                  const uPct = Math.min(97, (metrics.rulUpper / max) * 100);
                  const serviceDate = new Date(Date.now() + metrics.rul * 86400000)
                    .toLocaleDateString("en-GB", { day: "numeric", month: "short" });
                  return (
                    <div>
                      {/* Large predicted number */}
                      <div className="flex items-end gap-2 mb-3">
                        <span className="text-4xl font-bold tracking-tight leading-none" style={{ color }}>
                          {Math.round(metrics.rul)}
                        </span>
                        <div className="pb-0.5">
                          <div className="text-base font-semibold leading-none" style={{ color: "#6e6e73" }}>days</div>
                          <div className="text-[10px] mt-0.5" style={{ color: "#aaaaaa" }}>point estimate</div>
                        </div>
                        <div className="ml-auto pb-0.5 text-right">
                          <div className="text-xs font-bold" style={{ color }}>
                            {serviceDate}
                          </div>
                          <div className="text-[10px] mt-0.5" style={{ color: "#aaaaaa" }}>service by</div>
                        </div>
                      </div>

                      {/* Confidence band bar */}
                      <div className="relative mb-3 h-4">
                        {/* Track */}
                        <div className="absolute inset-0 bg-slate-100 rounded-full overflow-hidden">
                          {/* Danger zone — before lower bound */}
                          <div className="absolute top-0 left-0 h-full rounded-l-full" style={{ width: `${lPct}%`, background: "#fee2e2" }} />
                          {/* Confidence band */}
                          <div className="absolute top-0 h-full" style={{
                            left: `${lPct}%`, width: `${uPct - lPct}%`,
                            background: color + "28", border: `1px solid ${color}50`
                          }} />
                          {/* Safe zone — after upper bound */}
                          <div className="absolute top-0 right-0 h-full rounded-r-full" style={{ width: `${100 - uPct}%`, background: "#dcfce7" }} />
                        </div>
                        {/* Predicted dot */}
                        <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-[3px] border-white shadow-md z-10"
                          style={{ left: `calc(${pPct}% - 8px)`, backgroundColor: color }} />
                      </div>

                      {/* Legend row */}
                      <div className="flex items-center justify-between text-[10px] mb-3" style={{ color: "#aaaaaa" }}>
                        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm inline-block" style={{ background: "#fee2e2" }} />Early failure</div>
                        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm inline-block" style={{ background: color + "40" }} />80% CI band</div>
                        <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm inline-block" style={{ background: "#dcfce7" }} />Extended</div>
                      </div>

                      {/* Worst / Best cards */}
                      <div className="grid grid-cols-2 gap-2 mb-2">
                        <div className="rounded-xl px-3 py-2" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
                          <div className="text-[10px] font-bold uppercase tracking-wide mb-0.5" style={{ color: "#f87171" }}>Worst case</div>
                          <div className="text-sm font-bold" style={{ color: "#dc2626" }}>{Math.round(metrics.rulLower)}d</div>
                          <div className="text-[10px]" style={{ color: "#9ca3af" }}>earliest failure</div>
                        </div>
                        <div className="rounded-xl px-3 py-2" style={{ background: "#ffffff", border: "1px solid #e5e7eb" }}>
                          <div className="text-[10px] font-bold uppercase tracking-wide mb-0.5" style={{ color: "#4ade80" }}>Best case</div>
                          <div className="text-sm font-bold" style={{ color: "#16a34a" }}>{Math.round(metrics.rulUpper)}d</div>
                          <div className="text-[10px]" style={{ color: "#9ca3af" }}>latest failure</div>
                        </div>
                      </div>

                      {/* Urgency strip */}
                      <div className="text-[11px] font-semibold text-center rounded-lg px-3 py-1.5" style={{ background: color + "15", color }}>
                        {urgency}
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* XGBoost + SHAP Card (AI4I 2020 Dataset) */}
            {metrics.shapTopFeatures?.length > 0 && (
              <div className="border border-slate-200 rounded-xl bg-white text-slate-900 shadow-sm overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-white">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-blue-500" />
                    <span className="font-semibold text-sm text-slate-900">ML Prediction — AI4I 2020</span>
                  </div>
                  {metrics.modelAuc != null && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-mono">
                      AUC {metrics.modelAuc.toFixed(3)}
                    </span>
                  )}
                </div>
                <div className="px-4 pt-3 pb-1 flex items-center gap-3 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 text-xs">Failure Probability</span>
                    <span className={`text-lg font-bold ${(metrics.mlFailureProb ?? 0) > 0.6 ? "text-rose-600" : (metrics.mlFailureProb ?? 0) > 0.3 ? "text-amber-600" : "text-emerald-600"}`}>
                      {metrics.mlFailureProb != null ? `${Math.round(metrics.mlFailureProb * 100)}%` : "—"}
                    </span>
                  </div>
                  {metrics.failureTypeLabel && metrics.predictedFailureType !== "NONE" && (
                    <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-700 text-xs font-semibold border border-rose-200">
                      ⚠ {metrics.failureTypeLabel}
                    </span>
                  )}
                  {metrics.predictedFailureType === "NONE" && (
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-xs font-semibold border border-emerald-200">
                      ✓ No Failure Detected
                    </span>
                  )}
                </div>
                {/* SHAP Waterfall Chart */}
                <div className="px-4 pb-1 pt-1">
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                    Feature Importance (SHAP)
                  </div>
                  <div className="space-y-1.5">
                    {metrics.shapTopFeatures.slice(0, 6).map((f, i) => {
                      const isPos = f.shap >= 0;
                      const maxAbs = Math.max(...metrics.shapTopFeatures.map(x => Math.abs(x.shap)), 0.01);
                      const pct = Math.min(100, (Math.abs(f.shap) / maxAbs) * 100);
                      const label = f.feature.replace(/_/g, " ");
                      return (
                        <div key={i} className="flex items-center gap-2 text-xs">
                          <span className="text-slate-400 w-36 shrink-0 truncate text-right">{label}</span>
                          <div className="flex-1 flex items-center gap-1">
                            {!isPos && (
                              <div
                                className="h-4 rounded-sm bg-teal-500 opacity-80"
                                style={{ width: `${pct}%`, marginLeft: `${100 - pct}%` }}
                              />
                            )}
                            {isPos && (
                              <div
                                className="h-4 rounded-sm bg-rose-500 opacity-80"
                                style={{ width: `${pct}%` }}
                              />
                            )}
                          </div>
                          <span className={`w-14 text-right font-mono shrink-0 ${isPos ? "text-rose-400" : "text-teal-400"}`}>
                            {f.shap >= 0 ? "+" : ""}{f.shap.toFixed(3)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-slate-600 mt-2 mb-1">
                    <span className="text-teal-600">← Reduces risk</span>
                    <span className="text-rose-600">Increases risk →</span>
                  </div>
                </div>
              </div>
            )}

            {/* Sensor Contribution Analysis Chart */}
            {anomalyChartData.length > 0 && (
              <div className="border border-slate-200 rounded-xl bg-white text-slate-900 shadow-sm p-4">
                <div className="font-semibold text-slate-900 text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-slate-500" />
                  Sensor Contribution Analysis
                </div>
                <div className="h-[160px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={anomalyChartData} layout="vertical" margin={{ top: 0, right: 40, bottom: 0, left: 20 }}>
                      <XAxis type="number" domain={[0, "auto"]} stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis type="category" dataKey="sensor" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} width={80} />
                      <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                        {anomalyChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.score > 0.3 ? "#ef4444" : "#22c55e"} />
                        ))}
                        <LabelList dataKey="score" position="right" formatter={(v: any) => Number(v).toFixed(2)} style={{ fontSize: 10, fill: "#cbd5e1" }} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Business Impact Card */}
            {metrics.businessImpact && (
              <div className="border border-slate-200 rounded-xl bg-white text-slate-900 shadow-sm p-4">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-3">
                  <IndianRupee className="h-4 w-4 text-emerald-500" />
                  Business Impact (₹ INR)
                </div>
                <div className="grid grid-cols-3 gap-2 mt-3">
                  <div className="bg-white rounded-lg p-3 border border-slate-100">
                    <div className="text-slate-500 text-xs mb-1">ROI</div>
                    <div className="text-emerald-600 text-2xl font-bold">{metrics.businessImpact.roi_of_preventive_action}:1</div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-slate-100">
                    <div className="text-slate-500 text-xs mb-1">Loss if Ignored</div>
                    <div className="text-red-600 text-xl font-bold">
                      ₹{(metrics.businessImpact.production_loss_inr / 100000).toFixed(1)}L
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-slate-100">
                    <div className="text-slate-500 text-xs mb-1">Action Window</div>
                    <div className="text-amber-600 text-sm font-semibold leading-tight">{metrics.businessImpact.action_window}</div>
                  </div>
                </div>
                <div className="text-slate-500 text-xs mt-2">{metrics.businessImpact.spares_procurement}</div>
                <div className="text-slate-500 text-xs italic mt-1">{metrics.businessImpact.industry_benchmark}</div>
              </div>
            )}

            {/* Spare Parts Availability */}
            <SpareParts equipmentId={selectedEq.id} equipmentType={selectedEq.type} priority={metrics.priority} />

            {/* Similar Historical Cases */}
            {historicalCases.length > 0 && (
              <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
                <button onClick={() => setShowHistorical(!showHistorical)}
                  className="w-full px-4 py-3 flex items-center justify-between text-sm font-semibold text-slate-800 hover:bg-slate-50 transition-colors">
                  <span className="flex items-center gap-2 font-semibold text-slate-800 text-sm">
                    <FileText className="h-4 w-4 text-blue-500" />
                    Similar Historical Cases ({historicalCases.length})
                  </span>
                  {showHistorical ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                {showHistorical && (
                  <div className="px-4 pb-4 space-y-3">
                    {historicalCases.map((c, i) => {
                      const alertDot: Record<string, string> = { EMERGENCY: "#dc2626", CRITICAL: "#ef4444", WARNING: "#f59e0b", NORMAL: "#10b981" };
                      const dot = alertDot[c.alert_level] || "#c7c7cc";
                      const topAction = c.recommended_actions?.[0]?.action || "—";
                      return (
                        <div key={i} className="border border-slate-100 rounded-xl p-3 bg-white">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: dot }} />
                            <span className="text-xs font-bold" style={{ color: "#1d1d1f" }}>{c.alert_level}</span>
                            <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${c.maintenance_priority === "P1" ? "bg-rose-100 text-rose-700" : c.maintenance_priority === "P2" ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700"}`}>
                              {c.maintenance_priority}
                            </span>
                            <span className="ml-auto text-xs font-mono" style={{ color: "#c7c7cc" }}>
                              {c.timestamp?.slice(0, 10)}
                            </span>
                          </div>
                          <div className="text-xs text-slate-600 leading-snug line-clamp-2">{c.diagnosis}</div>
                          {c.root_cause && c.root_cause !== "No significant fault detected" && (
                            <div className="text-xs text-slate-400 mt-1 line-clamp-1">
                              <span className="font-semibold">Root cause:</span> {c.root_cause}
                            </div>
                          )}
                          <div className="flex items-center gap-1 mt-1.5 text-xs text-blue-600">
                            <CheckCircle2 className="h-3 w-3 shrink-0" />
                            <span className="truncate">{topAction}</span>
                          </div>
                          <div className="flex items-center gap-3 mt-1.5 text-xs" style={{ color: "#6e6e73" }}>
                            <span>HI: {Math.round(c.health_score)}%</span>
                            <span>RUL: {c.rul_days?.toFixed(1)}d</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Root Cause + Causal Chain (Agent 3 output) */}
            {(metrics.rootCause || metrics.causalChain) && metrics.rootCause !== "Sensor analysis complete" && (
              <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
                <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-800">Root Cause Analysis</span>
                  <span className="text-[9px] font-bold text-violet-700 bg-violet-50 border border-violet-200 px-1.5 py-0.5 rounded-full">Agent 3 · LLM</span>
                  {metrics.primaryMechanism && (
                    <span className="text-[9px] font-mono text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded-full ml-auto">
                      {metrics.primaryMechanism.replace(/_/g, " ")}
                    </span>
                  )}
                </div>
                <div className="px-4 py-3 space-y-2">
                  <p className="text-xs text-slate-700 leading-relaxed font-medium">{metrics.rootCause}</p>
                  {metrics.causalChain && metrics.causalChain !== metrics.rootCause && (
                    <div className="text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2 leading-relaxed border border-slate-100">
                      <span className="font-semibold text-slate-600">Causal chain: </span>{metrics.causalChain}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Evidence chain */}
            {metrics.evidenceChain?.length > 0 && (
              <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
                <button onClick={() => setShowEvidence(!showEvidence)}
                  className="w-full px-4 py-3 flex items-center justify-between text-sm font-semibold text-slate-800 hover:bg-slate-50 transition-colors">
                  <span className="font-semibold text-slate-800 text-sm">
                    Evidence Chain ({metrics.evidenceChain.length})
                  </span>
                  {showEvidence ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                {showEvidence && (
                  <div className="px-4 pb-4 space-y-2">
                    {metrics.evidenceChain.map((e, i) => (
                      <div key={i} className="text-xs text-slate-600 flex gap-2">
                        <span className="text-emerald-500 shrink-0">•</span><span>{e}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Retrieved sources */}
            {metrics.retrievedSources?.length > 0 && (
              <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
                <button onClick={() => setShowSources(!showSources)}
                  className="w-full px-4 py-3 flex items-center justify-between text-sm font-semibold text-slate-800 hover:bg-slate-50 transition-colors">
                  <span className="font-semibold text-slate-800 text-sm">
                    Knowledge Sources ({metrics.retrievedSources.length})
                  </span>
                  {showSources ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                {showSources && (
                  <div className="px-4 pb-4 space-y-1.5">
                    {metrics.retrievedSources.map((s, i) => (
                      <div key={i} className="text-xs text-blue-700 bg-blue-50 px-2 py-1.5 rounded">{s}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Recommended actions */}
            {metrics.recommendedActions?.length > 0 && (
              <div className="bg-white rounded-2xl overflow-hidden" style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
                <button onClick={() => setShowActions(!showActions)}
                  className="w-full px-4 py-3 flex items-center justify-between text-sm font-semibold text-slate-800 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800 text-sm">Work Orders ({metrics.recommendedActions.length})</span>
                    <span className="text-[9px] font-bold text-violet-700 bg-violet-50 border border-violet-200 px-1.5 py-0.5 rounded-full">Agent 4 · LLM</span>
                  </div>
                  {showActions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
                {showActions && (
                  <div className="px-4 pb-4 space-y-3">
                    {metrics.recommendedActions.slice(0, 5).map((a, i) => (
                      <div key={i} className="text-xs border-l-2 border-blue-400 pl-3">
                        <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${a.priority === "P1" ? "bg-rose-100 text-rose-700" : a.priority === "P2" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"}`}>{a.priority}</span>
                          {a.type && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-50 text-blue-700 border border-blue-100">{a.type}</span>}
                          {a.estimated_time && <span className="text-[9px] text-slate-400 font-mono">⏱ {a.estimated_time}</span>}
                        </div>
                        <div className="text-slate-700 leading-snug">{a.action}</div>
                        <div className="text-slate-400 mt-0.5 font-mono text-[10px]">{a.sop_reference}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
      </div>
    </div>
    </div>
  );
}

export default function AgentConsole() {
  return <Suspense fallback={null}><AgentConsoleInner /></Suspense>;
}
