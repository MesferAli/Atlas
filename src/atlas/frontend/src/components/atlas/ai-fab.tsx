"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Sparkles,
  X,
  Send,
  Loader2,
  FileBarChart,
  AlertTriangle,
  Zap,
  TrendingUp,
  ShieldCheck,
  RotateCcw,
  Download,
  ChevronRight,
  Bot,
  Lightbulb,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiRequest } from "@/lib/queryClient";

// ── Quick action definitions ────────────────────────────────────────
interface QuickAction {
  id: string;
  icon: React.ElementType;
  label: string;
  labelAr: string;
  description: string;
  prompt: string;
  color: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: "report",
    icon: FileBarChart,
    label: "Daily Report",
    labelAr: "تقرير يومي",
    description: "Generate a summary of today's operations",
    prompt:
      "Generate a daily operations summary: total queries processed, security events, top accessed tables, and any anomalies detected today.",
    color: "text-blue-500",
  },
  {
    id: "anomaly",
    icon: AlertTriangle,
    label: "Detect Anomalies",
    labelAr: "كشف الأخطاء",
    description: "Scan for unusual patterns in recent queries",
    prompt:
      "Analyze recent query patterns and identify any anomalies: unusual access times, high-frequency table scans, failed authentication attempts, or queries approaching restricted data.",
    color: "text-amber-500",
  },
  {
    id: "optimize",
    icon: Zap,
    label: "Optimize Queries",
    labelAr: "تحسين الاستعلامات",
    description: "Suggest performance improvements",
    prompt:
      "Review the most frequently executed queries and suggest optimizations: missing indexes, query rewrites, caching opportunities, or pagination improvements.",
    color: "text-violet-500",
  },
  {
    id: "forecast",
    icon: TrendingUp,
    label: "Usage Forecast",
    labelAr: "توقعات الاستخدام",
    description: "Predict resource usage trends",
    prompt:
      "Based on current usage patterns, forecast the next 7 days: expected query volume, peak hours, storage growth, and recommend capacity adjustments.",
    color: "text-emerald-500",
  },
  {
    id: "compliance",
    icon: ShieldCheck,
    label: "PDPL Audit",
    labelAr: "تدقيق PDPL",
    description: "Run a compliance check against PDPL rules",
    prompt:
      "Run a PDPL compliance audit: check for unmasked PII in recent query results, verify data classification enforcement, confirm audit log integrity, and flag any policy violations.",
    color: "text-rose-500",
  },
];

// ── Types ───────────────────────────────────────────────────────────
interface AIResponse {
  generated_sql: string;
  relevant_tables: Array<{
    table_name: string;
    owner: string;
    comments: string | null;
    score: number;
  }>;
  results: Array<Record<string, unknown>> | null;
  error: string | null;
  question: string;
}

interface InsightCard {
  id: string;
  action: QuickAction;
  response?: AIResponse;
  isLoading: boolean;
  timestamp: Date;
}

// ── Component ───────────────────────────────────────────────────────
export function AIFab() {
  const [open, setOpen] = useState(false);
  const [freeText, setFreeText] = useState("");
  const [insights, setInsights] = useState<InsightCard[]>([]);
  const panelRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target as Node)
      ) {
        // Don't close if clicking the FAB itself
        const fab = document.getElementById("atlas-ai-fab");
        if (fab?.contains(e.target as Node)) return;
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const mutation = useMutation({
    mutationFn: async (question: string) => {
      const res = await apiRequest("POST", "/v1/chat", { question });
      return res.json() as Promise<AIResponse>;
    },
  });

  const runAction = (action: QuickAction) => {
    const id = crypto.randomUUID();
    const card: InsightCard = {
      id,
      action,
      isLoading: true,
      timestamp: new Date(),
    };
    setInsights((prev) => [card, ...prev]);

    mutation.mutate(action.prompt, {
      onSuccess: (data) => {
        setInsights((prev) =>
          prev.map((c) =>
            c.id === id ? { ...c, response: data, isLoading: false } : c
          )
        );
      },
      onError: (err: Error) => {
        setInsights((prev) =>
          prev.map((c) =>
            c.id === id
              ? {
                  ...c,
                  isLoading: false,
                  response: {
                    question: action.prompt,
                    generated_sql: "",
                    relevant_tables: [],
                    results: null,
                    error: err.message,
                  },
                }
              : c
          )
        );
      },
    });
  };

  const handleFreeText = () => {
    const q = freeText.trim();
    if (!q) return;
    runAction({
      id: "custom",
      icon: Lightbulb,
      label: "Custom Query",
      labelAr: "استعلام مخصص",
      description: q,
      prompt: q,
      color: "text-primary",
    });
    setFreeText("");
  };

  return (
    <>
      {/* Floating Button */}
      <button
        id="atlas-ai-fab"
        onClick={() => setOpen(!open)}
        className={`fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg transition-all duration-300 ${
          open
            ? "bg-muted text-foreground rotate-0 shadow-md"
            : "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground hover:shadow-xl hover:scale-105"
        }`}
      >
        {open ? (
          <X className="h-5 w-5" />
        ) : (
          <Sparkles className="h-5 w-5" />
        )}
      </button>

      {/* Panel */}
      {open && (
        <div
          ref={panelRef}
          className="fixed bottom-24 right-6 z-50 w-[400px] max-h-[calc(100vh-8rem)] rounded-2xl border bg-card shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 fade-in duration-200"
        >
          {/* Header */}
          <div className="px-5 py-4 border-b bg-gradient-to-r from-card to-muted/30">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/70">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
              <div>
                <h3 className="text-sm font-semibold">Atlas AI</h3>
                <p className="text-[10px] text-muted-foreground">
                  Operational intelligence at your fingertips
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions Grid */}
          <div className="px-4 py-3 border-b">
            <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2.5">
              Quick Actions
            </p>
            <div className="grid grid-cols-5 gap-1.5">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.id}
                  onClick={() => runAction(action)}
                  disabled={mutation.isPending}
                  className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-muted/60 transition-colors group disabled:opacity-50"
                  title={action.description}
                >
                  <div className={`${action.color} group-hover:scale-110 transition-transform`}>
                    <action.icon className="h-4 w-4" />
                  </div>
                  <span className="text-[9px] text-muted-foreground group-hover:text-foreground text-center leading-tight">
                    {action.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Insights Feed */}
          <ScrollArea className="flex-1 min-h-0" ref={scrollRef}>
            <div className="p-4 space-y-3">
              {insights.length === 0 && (
                <div className="text-center py-8 space-y-2">
                  <Lightbulb className="h-8 w-8 text-muted-foreground/30 mx-auto" />
                  <p className="text-xs text-muted-foreground">
                    Run an action or ask a question to get AI insights
                  </p>
                </div>
              )}

              {insights.map((card) => (
                <InsightCardView key={card.id} card={card} onRetry={() => runAction(card.action)} />
              ))}
            </div>
          </ScrollArea>

          {/* Free-text Input */}
          <div className="px-4 py-3 border-t bg-card/50">
            <div className="relative">
              <Textarea
                placeholder="Ask anything about operations..."
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleFreeText();
                  }
                }}
                className="min-h-[40px] max-h-[80px] resize-none pr-10 text-xs rounded-xl border-border/50 bg-muted/30"
                rows={1}
              />
              <Button
                size="icon"
                variant="ghost"
                disabled={!freeText.trim() || mutation.isPending}
                onClick={handleFreeText}
                className="absolute bottom-1 right-1 h-7 w-7"
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Insight Card ────────────────────────────────────────────────────
function InsightCardView({
  card,
  onRetry,
}: {
  card: InsightCard;
  onRetry: () => void;
}) {
  const { action, response, isLoading } = card;
  const Icon = action.icon;

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border/30 bg-muted/20 p-3">
        <div className="flex items-center gap-2 mb-2">
          <Icon className={`h-3.5 w-3.5 ${action.color}`} />
          <span className="text-xs font-medium">{action.label}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          Analyzing...
        </div>
      </div>
    );
  }

  if (response?.error) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-3">
        <div className="flex items-center gap-2 mb-2">
          <Icon className={`h-3.5 w-3.5 ${action.color}`} />
          <span className="text-xs font-medium">{action.label}</span>
        </div>
        <p className="text-xs text-destructive mb-2">{response.error}</p>
        <button
          onClick={onRetry}
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        >
          <RotateCcw className="h-3 w-3" />
          Retry
        </button>
      </div>
    );
  }

  const sql = response?.generated_sql || "";
  const tables = response?.relevant_tables || [];
  const results = response?.results;
  const rowCount = results?.length ?? 0;

  return (
    <div className="rounded-xl border border-border/30 bg-card p-3 space-y-2 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`h-3.5 w-3.5 ${action.color}`} />
          <span className="text-xs font-medium">{action.label}</span>
        </div>
        <span className="text-[9px] text-muted-foreground font-mono">
          {card.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* Tables */}
      {tables.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {tables.map((t) => (
            <Badge
              key={t.table_name}
              variant="secondary"
              className="text-[9px] font-mono px-1.5 py-0"
            >
              {t.table_name}
            </Badge>
          ))}
        </div>
      )}

      {/* SQL preview */}
      {sql && (
        <pre className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 bg-muted/40 rounded-lg px-2.5 py-1.5 overflow-x-auto leading-relaxed whitespace-pre-wrap">
          {sql.length > 200 ? sql.slice(0, 200) + "..." : sql}
        </pre>
      )}

      {/* Result summary */}
      {results !== null && results !== undefined && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">
            {rowCount} row{rowCount !== 1 ? "s" : ""} returned
          </span>
          <button className="flex items-center gap-1 text-[10px] text-primary hover:underline">
            <Download className="h-3 w-3" />
            Export
          </button>
        </div>
      )}
    </div>
  );
}
