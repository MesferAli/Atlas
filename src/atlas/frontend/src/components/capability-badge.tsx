import { Badge } from "@/components/ui/badge";
import { Eye, Edit, FileEdit, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface CapabilityBadgeProps {
  capability: "read" | "list" | "create_draft" | "update_draft" | "unknown";
  isSupported?: boolean;
  size?: "sm" | "default";
}

const capabilityConfig = {
  read: {
    label: "Read",
    icon: Eye,
    className: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  },
  list: {
    label: "List",
    icon: Eye,
    className: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  create_draft: {
    label: "Draft Create",
    icon: FileEdit,
    className: "bg-chart-4/10 text-chart-4 border-chart-4/20",
  },
  update_draft: {
    label: "Draft Update",
    icon: Edit,
    className: "bg-chart-5/10 text-chart-5 border-chart-5/20",
  },
  unknown: {
    label: "Unknown",
    icon: X,
    className: "bg-muted text-muted-foreground border-muted",
  },
};

export function CapabilityBadge({ 
  capability, 
  isSupported = true,
  size = "default" 
}: CapabilityBadgeProps) {
  const config = capabilityConfig[capability] || capabilityConfig.unknown;
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border font-medium",
        isSupported ? config.className : "bg-muted/50 text-muted-foreground border-muted opacity-50",
        size === "sm" && "text-xs px-1.5 py-0"
      )}
    >
      {isSupported ? (
        <Icon className={cn("h-3 w-3", size === "sm" && "h-2.5 w-2.5")} />
      ) : (
        <X className={cn("h-3 w-3", size === "sm" && "h-2.5 w-2.5")} />
      )}
      {config.label}
    </Badge>
  );
}
