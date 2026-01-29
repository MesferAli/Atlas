import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Database,
  Shield,
  ArrowUpRight,
  Server,
  Lock,
  Globe,
  Cpu,
  BarChart3,
  Clock,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Eye,
  FileBarChart,
} from "lucide-react";
import { Link } from "wouter";
import { ScrollArea } from "@/components/ui/scroll-area";

// ── Stat Card ───────────────────────────────────────────────────────
function StatCard({
  icon: Icon,
  label,
  value,
  subtitle,
  trend,
  gradient,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  subtitle?: string;
  trend?: { value: string; up: boolean };
  gradient: string;
}) {
  return (
    <Card className="relative overflow-hidden border-0 shadow-sm hover:shadow-md transition-shadow duration-300">
      <div className={`absolute inset-0 opacity-[0.03] ${gradient}`} />
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {label}
            </p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl ${gradient} shadow-sm`}
          >
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
        {trend && (
          <div className="mt-3 flex items-center gap-1.5">
            <span
              className={`inline-flex items-center text-xs font-medium ${
                trend.up
                  ? "text-green-600 dark:text-green-400"
                  : "text-amber-600 dark:text-amber-400"
              }`}
            >
              {trend.up ? (
                <TrendingUp className="h-3 w-3 mr-0.5" />
              ) : (
                <Activity className="h-3 w-3 mr-0.5" />
              )}
              {trend.value}
            </span>
            <span className="text-xs text-muted-foreground">vs last week</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Proactive Insight Card ──────────────────────────────────────────
function InsightRow({
  icon: Icon,
  color,
  title,
  description,
  time,
}: {
  icon: React.ElementType;
  color: string;
  title: string;
  description: string;
  time: string;
}) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/40 transition-colors group">
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${color} bg-opacity-10`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium">{title}</p>
        <p className="text-[11px] text-muted-foreground leading-relaxed mt-0.5 line-clamp-2">
          {description}
        </p>
      </div>
      <span className="text-[10px] text-muted-foreground font-mono shrink-0 mt-0.5">{time}</span>
    </div>
  );
}

// ── Main Dashboard ──────────────────────────────────────────────────
export default function Dashboard() {
  const { data: securityData } = useQuery<{
    security_mode: string;
    read_only_enforced: boolean;
    thin_mode_enabled: boolean;
    blocked_operations: string[];
  }>({ queryKey: ["/v1/security"] });

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Operations Center"
        description="Atlas AI — Proactive operational intelligence"
        actions={
          <Link href="/settings">
            <Button variant="outline" size="sm" className="gap-2">
              <Server className="h-3.5 w-3.5" />
              Configure
            </Button>
          </Link>
        }
      />

      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={Database}
              label="Oracle Status"
              value="Connected"
              subtitle="Thin Mode (no client)"
              trend={{ value: "99.9% uptime", up: true }}
              gradient="bg-gradient-to-br from-blue-500 to-blue-600"
            />
            <StatCard
              icon={Shield}
              label="PDPL Compliance"
              value="Active"
              subtitle="All checks passing"
              trend={{ value: "0 violations", up: true }}
              gradient="bg-gradient-to-br from-emerald-500 to-emerald-600"
            />
            <StatCard
              icon={Cpu}
              label="AI Model"
              value="Qwen 7B"
              subtitle="4-bit quantized"
              gradient="bg-gradient-to-br from-violet-500 to-violet-600"
            />
            <StatCard
              icon={BarChart3}
              label="Queries Today"
              value="24"
              subtitle="Read-only enforced"
              trend={{ value: "+12%", up: true }}
              gradient="bg-gradient-to-br from-amber-500 to-amber-600"
            />
          </div>

          {/* Main Content: 2 columns */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Proactive Insights + Recent Queries */}
            <div className="lg:col-span-2 space-y-6">
              {/* AI Proactive Insights */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Zap className="h-4 w-4 text-violet-500" />
                    AI Proactive Insights
                    <Badge variant="secondary" className="text-[9px] ml-auto">
                      Live
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 pt-0">
                  <InsightRow
                    icon={AlertTriangle}
                    color="text-amber-500"
                    title="Unusual access pattern detected"
                    description="3x spike in HR_EMPLOYEES queries from non-HR users in the last hour. Recommend reviewing access policies."
                    time="12m ago"
                  />
                  <InsightRow
                    icon={TrendingUp}
                    color="text-emerald-500"
                    title="Query optimization opportunity"
                    description="PO_HEADERS sequential scans can be reduced 60% by adding index on VENDOR_ID. Estimated saving: 2.3s/query."
                    time="1h ago"
                  />
                  <InsightRow
                    icon={Shield}
                    color="text-blue-500"
                    title="PDPL audit passed"
                    description="Scheduled PDPL compliance scan completed — 0 unmasked PII found in recent query results across all tables."
                    time="3h ago"
                  />
                  <InsightRow
                    icon={FileBarChart}
                    color="text-rose-500"
                    title="Daily report ready"
                    description="Operations summary generated: 24 queries processed, 0 security events, top table: AP_INVOICES_ALL."
                    time="6h ago"
                  />
                </CardContent>
              </Card>

              {/* Recent Operations */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Clock className="h-4 w-4 text-amber-500" />
                    Recent Operations
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    {[
                      { query: "Top 10 employees by salary", tables: "HR_EMPLOYEES", status: "success", rows: 10, time: "2m ago" },
                      { query: "Active purchase orders this month", tables: "PO_HEADERS_ALL", status: "success", rows: 47, time: "18m ago" },
                      { query: "عرض الفواتير المعلقة", tables: "AP_INVOICES_ALL", status: "success", rows: 12, time: "45m ago" },
                      { query: "Department headcount report", tables: "HR_EMPLOYEES, HR_DEPARTMENTS", status: "success", rows: 8, time: "1h ago" },
                      { query: "Delete old records", tables: "—", status: "blocked", rows: 0, time: "2h ago" },
                    ].map((op, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-muted/40 transition-colors"
                      >
                        <div className={`h-2 w-2 rounded-full shrink-0 ${
                          op.status === "success" ? "bg-emerald-500" : "bg-red-500"
                        }`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium truncate">{op.query}</p>
                          <p className="text-[10px] text-muted-foreground font-mono">{op.tables}</p>
                        </div>
                        {op.status === "success" ? (
                          <Badge variant="secondary" className="text-[9px] font-mono px-1.5 py-0">
                            {op.rows} rows
                          </Badge>
                        ) : (
                          <Badge variant="destructive" className="text-[9px] px-1.5 py-0">
                            Blocked
                          </Badge>
                        )}
                        <span className="text-[10px] text-muted-foreground font-mono w-12 text-right shrink-0">
                          {op.time}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Right Sidebar */}
            <div className="space-y-4">
              {/* Security Status */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Lock className="h-4 w-4 text-emerald-500" />
                    Security Status
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    {[
                      "Query Mode — Read-Only",
                      "Data Moat — Enforced",
                      "Audit Logging — Active",
                      "PII Detection — Active",
                    ].map((item) => (
                      <div key={item} className="flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        <span className="text-xs">{item}</span>
                      </div>
                    ))}
                  </div>

                  {securityData?.blocked_operations && (
                    <div className="pt-2 border-t">
                      <p className="text-[10px] text-muted-foreground mb-2 uppercase tracking-wider font-medium">
                        Blocked Operations
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {securityData.blocked_operations.slice(0, 6).map((op) => (
                          <Badge
                            key={op}
                            variant="outline"
                            className="text-[9px] font-mono px-1.5 py-0 text-destructive/70 border-destructive/20"
                          >
                            {op}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Infrastructure */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Globe className="h-4 w-4 text-blue-500" />
                    Infrastructure
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    ["Region", "Riyadh (SA)"],
                    ["Cloud", "Alibaba ACK"],
                    ["Vector DB", "Qdrant"],
                  ].map(([label, val]) => (
                    <div key={label} className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{label}</span>
                      <span className="text-xs font-medium">{val}</span>
                    </div>
                  ))}
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Tunnel</span>
                    <Badge
                      variant="outline"
                      className="text-[10px] gap-1 border-green-500/30 text-green-600 dark:text-green-400"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                      Secure
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Eye className="h-4 w-4 text-amber-500" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1.5">
                    {[
                      ["/audit", "View Audit Log"],
                      ["/settings", "System Settings"],
                      ["/help", "Documentation"],
                    ].map(([href, label]) => (
                      <Link key={href} href={href}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full justify-between h-9 text-xs font-normal"
                        >
                          {label}
                          <ArrowUpRight className="h-3 w-3 text-muted-foreground" />
                        </Button>
                      </Link>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
