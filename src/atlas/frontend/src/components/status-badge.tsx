import { Badge } from "@/components/ui/badge";
import { Check, Clock, X, Pause, AlertCircle, Loader2, Plug } from "lucide-react";
import { cn } from "@/lib/utils";

type StatusType = 
  | "pending" | "approved" | "rejected" | "deferred" 
  | "connected" | "error" | "disabled" 
  | "draft" | "active" | "archived"
  | "open" | "investigating" | "resolved" | "dismissed"
  | "in_progress" | "completed" | "abandoned";

interface StatusBadgeProps {
  status: StatusType;
  size?: "sm" | "default";
}

const statusConfig: Record<StatusType, { label: string; icon: typeof Check; className: string }> = {
  pending: {
    label: "Pending",
    icon: Clock,
    className: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  },
  approved: {
    label: "Approved",
    icon: Check,
    className: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  rejected: {
    label: "Rejected",
    icon: X,
    className: "bg-destructive/10 text-destructive border-destructive/20",
  },
  deferred: {
    label: "Deferred",
    icon: Pause,
    className: "bg-muted text-muted-foreground border-muted",
  },
  connected: {
    label: "Connected",
    icon: Plug,
    className: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  error: {
    label: "Error",
    icon: AlertCircle,
    className: "bg-destructive/10 text-destructive border-destructive/20",
  },
  disabled: {
    label: "Disabled",
    icon: Pause,
    className: "bg-muted text-muted-foreground border-muted",
  },
  draft: {
    label: "Draft",
    icon: Clock,
    className: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  },
  active: {
    label: "Active",
    icon: Check,
    className: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  archived: {
    label: "Archived",
    icon: Pause,
    className: "bg-muted text-muted-foreground border-muted",
  },
  open: {
    label: "Open",
    icon: AlertCircle,
    className: "bg-destructive/10 text-destructive border-destructive/20",
  },
  investigating: {
    label: "Investigating",
    icon: Loader2,
    className: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  },
  resolved: {
    label: "Resolved",
    icon: Check,
    className: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  dismissed: {
    label: "Dismissed",
    icon: X,
    className: "bg-muted text-muted-foreground border-muted",
  },
  in_progress: {
    label: "In Progress",
    icon: Loader2,
    className: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  },
  completed: {
    label: "Completed",
    icon: Check,
    className: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  abandoned: {
    label: "Abandoned",
    icon: X,
    className: "bg-muted text-muted-foreground border-muted",
  },
};

export function StatusBadge({ status, size = "default" }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border font-medium",
        config.className,
        size === "sm" && "text-xs px-1.5 py-0"
      )}
    >
      <Icon className={cn("h-3 w-3", size === "sm" && "h-2.5 w-2.5", status === "investigating" && "animate-spin")} />
      {config.label}
    </Badge>
  );
}
