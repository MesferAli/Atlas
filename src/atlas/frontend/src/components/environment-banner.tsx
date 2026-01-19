import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Server, Code } from "lucide-react";
import { useTranslations } from "@/lib/i18n";

type Environment = "production" | "staging" | "development";

interface EnvironmentResponse {
  environment: Environment;
}

export function EnvironmentBanner() {
  const t = useTranslations();
  const { data, isLoading } = useQuery<EnvironmentResponse>({
    queryKey: ["/api/settings/environment"],
  });

  if (isLoading || !data) {
    return null;
  }

  const environmentConfig: Record<Environment, {
    label: string;
    bgClass: string;
    textClass: string;
    icon: typeof Server;
  }> = {
    production: {
      label: t.environment.production,
      bgClass: "bg-destructive/10",
      textClass: "text-destructive",
      icon: AlertTriangle,
    },
    staging: {
      label: t.environment.staging,
      bgClass: "bg-chart-4/10",
      textClass: "text-chart-4",
      icon: Server,
    },
    development: {
      label: t.environment.development,
      bgClass: "bg-chart-2/10",
      textClass: "text-chart-2",
      icon: Code,
    },
  };

  const config = environmentConfig[data.environment];
  const Icon = config.icon;

  return (
    <div
      className={`flex items-center justify-center gap-2 px-4 py-2 ${config.bgClass} ${config.textClass} text-sm font-medium`}
      data-testid="banner-environment"
    >
      <Icon className="h-4 w-4" />
      <span>{config.label}</span>
    </div>
  );
}
