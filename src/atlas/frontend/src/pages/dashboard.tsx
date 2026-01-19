import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PriorityBadge } from "@/components/priority-badge";
import { StatusBadge } from "@/components/status-badge";
import { ConfidenceScore } from "@/components/confidence-score";
import {
  Package,
  Warehouse,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  Plug,
  TrendingUp,
  Clock,
  CheckCircle,
} from "lucide-react";
import { Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import type { Recommendation, Anomaly, Connector } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTranslations } from "@/lib/i18n";

export default function Dashboard() {
  const t = useTranslations();
  
  const { data: stats, isLoading: statsLoading } = useQuery<{
    items: number;
    locations: number;
    recommendations: number;
    anomalies: number;
    connectors: number;
    activeConnectors: number;
  }>({
    queryKey: ["/api/stats"],
  });

  const { data: recommendations, isLoading: recsLoading } = useQuery<Recommendation[]>({
    queryKey: ["/api/recommendations"],
  });
  const recentRecommendations = recommendations?.slice(0, 5);

  const { data: anomalies, isLoading: anomaliesLoading } = useQuery<Anomaly[]>({
    queryKey: ["/api/anomalies"],
  });
  const recentAnomalies = anomalies?.slice(0, 3);

  const { data: connectors, isLoading: connectorsLoading } = useQuery<Connector[]>({
    queryKey: ["/api/connectors"],
  });

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={t.dashboard.title}
        description={t.dashboard.description}
        actions={
          <Link href="/onboarding">
            <Button data-testid="button-start-onboarding">
              <Plug className="me-2 h-4 w-4" />
              {t.dashboard.connectNewSystem}
            </Button>
          </Link>
        }
      />

      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {statsLoading ? (
              <>
                {[1, 2, 3, 4].map((i) => (
                  <Card key={i}>
                    <CardContent className="p-6">
                      <Skeleton className="h-4 w-24 mb-2" />
                      <Skeleton className="h-9 w-16 mb-2" />
                      <Skeleton className="h-4 w-32" />
                    </CardContent>
                  </Card>
                ))}
              </>
            ) : (
              <>
                <StatCard
                  title={t.dashboard.activeItems}
                  value={stats?.items || 0}
                  change={12}
                  changeLabel="vs last month"
                  icon={<Package className="h-5 w-5" />}
                />
                <StatCard
                  title={t.dashboard.locations}
                  value={stats?.locations || 0}
                  icon={<Warehouse className="h-5 w-5" />}
                />
                <StatCard
                  title={t.dashboard.pendingRecommendations}
                  value={stats?.recommendations || 0}
                  change={-8}
                  changeLabel="actioned"
                  icon={<Lightbulb className="h-5 w-5" />}
                />
                <StatCard
                  title={t.dashboard.openAnomalies}
                  value={stats?.anomalies || 0}
                  icon={<AlertTriangle className="h-5 w-5" />}
                />
              </>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader className="flex flex-row items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-lg font-medium">{t.dashboard.aiRecommendations}</CardTitle>
                  <CardDescription>{t.dashboard.recentInsights}</CardDescription>
                </div>
                <Link href="/recommendations">
                  <Button variant="ghost" size="sm" data-testid="link-view-all-recommendations">
                    {t.dashboard.viewAll}
                    <ArrowRight className="ms-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {recsLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="flex items-start gap-4 p-4 rounded-lg border">
                        <Skeleton className="h-10 w-10 rounded-lg" />
                        <div className="flex-1 space-y-2">
                          <Skeleton className="h-4 w-3/4" />
                          <Skeleton className="h-3 w-1/2" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : recentRecommendations && recentRecommendations.length > 0 ? (
                  <div className="space-y-3">
                    {recentRecommendations.map((rec) => (
                      <div
                        key={rec.id}
                        className="flex items-start gap-4 p-4 rounded-lg border hover-elevate cursor-pointer"
                        data-testid={`recommendation-card-${rec.id}`}
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary shrink-0">
                          <Lightbulb className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium truncate">{rec.title}</span>
                            <PriorityBadge priority={rec.priority as "critical" | "high" | "medium" | "low"} size="sm" />
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {rec.description}
                          </p>
                          <div className="mt-2 w-32">
                            <ConfidenceScore score={rec.confidenceScore} size="sm" showLabel={false} />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <StatusBadge status={rec.status as "pending" | "approved" | "rejected" | "deferred"} size="sm" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
                      <CheckCircle className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="text-sm font-medium">{t.dashboard.allCaughtUp}</p>
                    <p className="text-sm text-muted-foreground">{t.dashboard.noPendingRecommendations}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-lg font-medium">{t.dashboard.systemHealth}</CardTitle>
                  <CardDescription>{t.dashboard.connectedSources}</CardDescription>
                </div>
                <Link href="/connectors">
                  <Button variant="ghost" size="sm" data-testid="link-view-connectors">
                    {t.dashboard.manage}
                    <ArrowRight className="ms-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {connectorsLoading ? (
                  <div className="space-y-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
                        <Skeleton className="h-8 w-8 rounded" />
                        <div className="flex-1">
                          <Skeleton className="h-4 w-24 mb-1" />
                          <Skeleton className="h-3 w-16" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : connectors && connectors.length > 0 ? (
                  <div className="space-y-3">
                    {connectors.slice(0, 4).map((connector) => (
                      <div
                        key={connector.id}
                        className="flex items-center gap-3 p-3 rounded-lg border"
                        data-testid={`connector-status-${connector.id}`}
                      >
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-muted">
                          <Plug className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{connector.name}</p>
                          <p className="text-xs text-muted-foreground truncate">{connector.baseUrl}</p>
                        </div>
                        <StatusBadge 
                          status={connector.status as "pending" | "connected" | "error" | "disabled"} 
                          size="sm" 
                        />
                      </div>
                    ))}
                    {connectors.length === 0 && (
                      <Link href="/onboarding">
                        <Button variant="outline" className="w-full" data-testid="button-add-first-connector">
                          <Plug className="me-2 h-4 w-4" />
                          {t.dashboard.addFirstConnector}
                        </Button>
                      </Link>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-6 text-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted mb-3">
                      <Plug className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{t.dashboard.noConnectorsConfigured}</p>
                    <Link href="/onboarding">
                      <Button size="sm" data-testid="button-setup-connector">
                        {t.dashboard.getStarted}
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-lg font-medium">{t.dashboard.anomaliesDetected}</CardTitle>
                  <CardDescription>{t.dashboard.unusualPatterns}</CardDescription>
                </div>
                <Link href="/anomalies">
                  <Button variant="ghost" size="sm" data-testid="link-view-all-anomalies">
                    {t.dashboard.viewAll}
                    <ArrowRight className="ms-2 h-4 w-4" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {anomaliesLoading ? (
                  <div className="space-y-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-lg border">
                        <Skeleton className="h-8 w-8 rounded" />
                        <div className="flex-1">
                          <Skeleton className="h-4 w-3/4 mb-1" />
                          <Skeleton className="h-3 w-1/2" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : recentAnomalies && recentAnomalies.length > 0 ? (
                  <div className="space-y-3">
                    {recentAnomalies.map((anomaly) => (
                      <div
                        key={anomaly.id}
                        className="flex items-start gap-3 p-3 rounded-lg border hover-elevate cursor-pointer"
                        data-testid={`anomaly-card-${anomaly.id}`}
                      >
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-destructive/10 text-destructive shrink-0">
                          <AlertTriangle className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium truncate">{anomaly.title}</span>
                            <PriorityBadge priority={anomaly.severity as "critical" | "high" | "medium" | "low"} size="sm" />
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {anomaly.description}
                          </p>
                        </div>
                        <StatusBadge 
                          status={anomaly.status as "open" | "investigating" | "resolved" | "dismissed"} 
                          size="sm" 
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-6 text-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-chart-2/10 mb-3">
                      <CheckCircle className="h-5 w-5 text-chart-2" />
                    </div>
                    <p className="text-sm font-medium">{t.dashboard.allClear}</p>
                    <p className="text-sm text-muted-foreground">{t.dashboard.noAnomaliesDetected}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-medium">{t.dashboard.quickActions}</CardTitle>
                <CardDescription>{t.dashboard.commonOperations}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  <Link href="/onboarding">
                    <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2" data-testid="quick-action-connect">
                      <Plug className="h-5 w-5" />
                      <span className="text-sm">{t.dashboard.connectSystem}</span>
                    </Button>
                  </Link>
                  <Link href="/mappings">
                    <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2" data-testid="quick-action-mapping">
                      <TrendingUp className="h-5 w-5" />
                      <span className="text-sm">{t.dashboard.createMapping}</span>
                    </Button>
                  </Link>
                  <Link href="/recommendations">
                    <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2" data-testid="quick-action-recommendations">
                      <Lightbulb className="h-5 w-5" />
                      <span className="text-sm">{t.dashboard.reviewAI}</span>
                    </Button>
                  </Link>
                  <Link href="/audit">
                    <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2" data-testid="quick-action-audit">
                      <Clock className="h-5 w-5" />
                      <span className="text-sm">{t.dashboard.viewAudit}</span>
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
