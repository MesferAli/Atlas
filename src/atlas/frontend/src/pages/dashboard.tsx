import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/page-header";
import { OracleChat } from "@/components/OracleChat";
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
} from "lucide-react";
import { Link } from "wouter";
import { ScrollArea } from "@/components/ui/scroll-area";

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
        title="Dashboard"
        description="Atlas AI Orchestration Platform"
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

          {/* Main Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Oracle Chat */}
            <div className="lg:col-span-2">
              <OracleChat />
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
                    <Clock className="h-4 w-4 text-amber-500" />
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
