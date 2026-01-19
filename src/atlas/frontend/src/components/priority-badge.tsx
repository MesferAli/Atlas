import { Badge } from "@/components/ui/badge";
import { AlertTriangle, AlertCircle, AlertOctagon, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface PriorityBadgeProps {
  priority: "critical" | "high" | "medium" | "low";
  size?: "sm" | "default";
}

const priorityConfig = {
  critical: {
    label: "Critical",
    icon: AlertOctagon,
    className: "bg-destructive/10 text-destructive border-destructive/20",
  },
  high: {
    label: "High",
    icon: AlertTriangle,
    className: "bg-chart-5/10 text-chart-5 border-chart-5/20",
  },
  medium: {
    label: "Medium",
    icon: AlertCircle,
    className: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  },
  low: {
    label: "Low",
    icon: Info,
    className: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  },
};

export function PriorityBadge({ priority, size = "default" }: PriorityBadgeProps) {
  const config = priorityConfig[priority];
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
      <Icon className={cn("h-3 w-3", size === "sm" && "h-2.5 w-2.5")} />
      {config.label}
    </Badge>
  );
}
