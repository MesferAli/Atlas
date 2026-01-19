import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  FileText,
  Search,
  ChevronDown,
  ChevronUp,
  User,
  Clock,
  Activity,
  Plus,
  Edit,
  Trash2,
  Check,
  X,
  LogIn,
  Eye,
  Link,
  Hash,
} from "lucide-react";
import { ExportButton } from "@/components/export-button";
import { auditLogColumns } from "@/lib/export-utils";
import { useQuery } from "@tanstack/react-query";
import type { AuditLog } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";

const actionIcons: Record<string, typeof Activity> = {
  create: Plus,
  update: Edit,
  delete: Trash2,
  approve: Check,
  reject: X,
  login: LogIn,
  view: Eye,
};

const actionColors: Record<string, string> = {
  create: "bg-chart-2/10 text-chart-2",
  update: "bg-chart-4/10 text-chart-4",
  delete: "bg-destructive/10 text-destructive",
  approve: "bg-chart-2/10 text-chart-2",
  reject: "bg-destructive/10 text-destructive",
  login: "bg-chart-1/10 text-chart-1",
  view: "bg-muted text-muted-foreground",
};

export default function Audit() {
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [resourceFilter, setResourceFilter] = useState<string>("all");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("all");
  const [correlationIdFilter, setCorrelationIdFilter] = useState<string>("");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const { data: auditLogs, isLoading } = useQuery<AuditLog[]>({
    queryKey: ["/api/audit-logs"],
  });

  const filteredLogs = auditLogs?.filter((log) => {
    const matchesSearch = 
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resourceType.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.userId?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.correlationId?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAction = actionFilter === "all" || log.action === actionFilter;
    const matchesResource = resourceFilter === "all" || log.resourceType === resourceFilter;
    const matchesEventType = eventTypeFilter === "all" || log.eventType === eventTypeFilter;
    const matchesCorrelationId = !correlationIdFilter || log.correlationId === correlationIdFilter;
    return matchesSearch && matchesAction && matchesResource && matchesEventType && matchesCorrelationId;
  });

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const uniqueActions = Array.from(new Set(auditLogs?.map(l => l.action) || []));
  const uniqueResources = Array.from(new Set(auditLogs?.map(l => l.resourceType) || []));
  const uniqueEventTypes = Array.from(new Set(auditLogs?.map(l => l.eventType).filter(Boolean) || []));

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Audit Log"
        description="Complete traceability of all platform actions"
        actions={
          <ExportButton
            title="Audit Log"
            subtitle="Complete traceability of all platform actions"
            filename="audit-log"
            columns={auditLogColumns}
            data={(filteredLogs || []) as Record<string, unknown>[]}
            formats={['pdf', 'excel', 'csv']}
          />
        }
      />

      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-light">{auditLogs?.length || 0}</p>
                    <p className="text-xs text-muted-foreground">Total Events</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-chart-2/10 text-chart-2">
                    <Plus className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-light">
                      {auditLogs?.filter(l => l.action === "create").length || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">Creates</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-chart-4/10 text-chart-4">
                    <Edit className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-light">
                      {auditLogs?.filter(l => l.action === "update").length || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">Updates</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-chart-2/10 text-chart-2">
                    <Check className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-light">
                      {auditLogs?.filter(l => l.action === "approve").length || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">Approvals</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div>
                  <CardTitle className="text-lg font-medium">Event History</CardTitle>
                  <CardDescription>
                    Immutable record of all signals, decisions, and actions
                  </CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search audit logs..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                      data-testid="input-search-audit"
                    />
                  </div>
                  <Select value={actionFilter} onValueChange={setActionFilter}>
                    <SelectTrigger className="w-32" data-testid="select-action-filter">
                      <SelectValue placeholder="Action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Actions</SelectItem>
                      {uniqueActions.map(action => (
                        <SelectItem key={action} value={action} className="capitalize">
                          {action}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={resourceFilter} onValueChange={setResourceFilter}>
                    <SelectTrigger className="w-36" data-testid="select-resource-filter">
                      <SelectValue placeholder="Resource" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Resources</SelectItem>
                      {uniqueResources.map(resource => (
                        <SelectItem key={resource} value={resource} className="capitalize">
                          {resource.replace(/_/g, " ")}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
                    <SelectTrigger className="w-40" data-testid="select-event-type-filter">
                      <SelectValue placeholder="Event Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Event Types</SelectItem>
                      {uniqueEventTypes.map(eventType => (
                        <SelectItem key={eventType} value={eventType} className="capitalize">
                          {String(eventType).replace(/_/g, " ")}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {correlationIdFilter && (
                <div className="flex items-center gap-2 mt-4">
                  <Badge variant="outline" className="text-xs">
                    <Link className="h-3 w-3 mr-1" />
                    Filtering by Correlation ID: {correlationIdFilter.slice(0, 8)}...
                  </Badge>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-6 px-2 text-xs"
                    onClick={() => setCorrelationIdFilter("")}
                    data-testid="button-clear-correlation-filter"
                  >
                    Clear
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
                      <Skeleton className="h-8 w-8 rounded" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-1/4" />
                        <Skeleton className="h-3 w-1/3" />
                      </div>
                      <Skeleton className="h-4 w-24" />
                    </div>
                  ))}
                </div>
              ) : filteredLogs && filteredLogs.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12"></TableHead>
                      <TableHead className="w-16">#</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Event Type</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Correlation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLogs.map((log) => {
                      const ActionIcon = actionIcons[log.action] || Activity;
                      const colorClass = actionColors[log.action] || "bg-muted text-muted-foreground";
                      const isExpanded = expandedRows.has(log.id);
                      const hasDetails = log.previousState || log.newState || log.metadata;

                      return (
                        <Collapsible key={log.id} open={isExpanded} onOpenChange={() => toggleRow(log.id)} asChild>
                          <>
                            <TableRow 
                              className={hasDetails ? "cursor-pointer" : ""}
                              data-testid={`audit-row-${log.id}`}
                            >
                              <TableCell>
                                {hasDetails && (
                                  <CollapsibleTrigger asChild>
                                    <Button variant="ghost" size="icon" className="h-6 w-6">
                                      {isExpanded ? (
                                        <ChevronUp className="h-4 w-4" />
                                      ) : (
                                        <ChevronDown className="h-4 w-4" />
                                      )}
                                    </Button>
                                  </CollapsibleTrigger>
                                )}
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-xs text-muted-foreground font-mono">
                                  <Hash className="h-3 w-3" />
                                  {log.sequenceNumber || "-"}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <div className={`flex h-7 w-7 items-center justify-center rounded ${colorClass}`}>
                                    <ActionIcon className="h-3.5 w-3.5" />
                                  </div>
                                  <span className="font-medium capitalize">{log.action}</span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className="text-xs capitalize">
                                  {log.eventType?.replace(/_/g, " ") || "action"}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Badge variant="secondary" className="text-xs capitalize">
                                    {log.resourceType.replace(/_/g, " ")}
                                  </Badge>
                                  {log.resourceId && (
                                    <code className="text-xs text-muted-foreground">
                                      {log.resourceId.slice(0, 8)}...
                                    </code>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <User className="h-4 w-4 text-muted-foreground" />
                                  <span className="text-sm">{log.userId || "System"}</span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Clock className="h-4 w-4 text-muted-foreground" />
                                  <span className="text-sm text-muted-foreground">
                                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : "-"}
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell>
                                {log.correlationId ? (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 px-2 text-xs font-mono"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setCorrelationIdFilter(log.correlationId!);
                                    }}
                                    data-testid={`button-filter-correlation-${log.id}`}
                                  >
                                    <Link className="h-3 w-3 mr-1" />
                                    {log.correlationId.slice(0, 8)}...
                                  </Button>
                                ) : (
                                  <span className="text-sm text-muted-foreground">-</span>
                                )}
                              </TableCell>
                            </TableRow>
                            {hasDetails && (
                              <CollapsibleContent asChild>
                                <TableRow className="bg-muted/30">
                                  <TableCell colSpan={8} className="p-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                      {log.previousState && (
                                        <div>
                                          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Previous State</p>
                                          <pre className="text-xs bg-background p-3 rounded-lg overflow-auto max-h-32 font-mono">
                                            {JSON.stringify(log.previousState as object, null, 2)}
                                          </pre>
                                        </div>
                                      )}
                                      {log.newState && (
                                        <div>
                                          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">New State</p>
                                          <pre className="text-xs bg-background p-3 rounded-lg overflow-auto max-h-32 font-mono">
                                            {JSON.stringify(log.newState as object, null, 2)}
                                          </pre>
                                        </div>
                                      )}
                                      {log.metadata && (
                                        <div className={!log.previousState && !log.newState ? "md:col-span-2" : ""}>
                                          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Metadata</p>
                                          <pre className="text-xs bg-background p-3 rounded-lg overflow-auto max-h-32 font-mono">
                                            {JSON.stringify(log.metadata as object, null, 2)}
                                          </pre>
                                        </div>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              </CollapsibleContent>
                            )}
                          </>
                        </Collapsible>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState
                  icon={FileText}
                  title="No audit logs found"
                  description={searchQuery || actionFilter !== "all" || resourceFilter !== "all" 
                    ? "Try adjusting your filters to see more results." 
                    : "Audit events will appear here as actions are performed in the platform."}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
