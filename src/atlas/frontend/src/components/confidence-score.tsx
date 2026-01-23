import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface ConfidenceScoreProps {
  score: number;
  size?: "sm" | "default" | "lg";
  showLabel?: boolean;
  className?: string;
}

export function ConfidenceScore({ 
  score, 
  size = "default",
  showLabel = true,
  className 
}: ConfidenceScoreProps) {
  const getScoreColor = () => {
    if (score >= 80) return "text-chart-2";
    if (score >= 60) return "text-chart-4";
    if (score >= 40) return "text-chart-5";
    return "text-destructive";
  };

  const getProgressColor = () => {
    if (score >= 80) return "[&>div]:bg-chart-2";
    if (score >= 60) return "[&>div]:bg-chart-4";
    if (score >= 40) return "[&>div]:bg-chart-5";
    return "[&>div]:bg-destructive";
  };

  const sizeConfig = {
    sm: { text: "text-sm", progress: "h-1.5" },
    default: { text: "text-lg", progress: "h-2" },
    lg: { text: "text-2xl", progress: "h-3" },
  };

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      {showLabel && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Confidence
          </span>
          <span className={cn("font-semibold", sizeConfig[size].text, getScoreColor())}>
            {score}%
          </span>
        </div>
      )}
      <Progress 
        value={score} 
        className={cn("bg-muted", sizeConfig[size].progress, getProgressColor())} 
      />
    </div>
  );
}
