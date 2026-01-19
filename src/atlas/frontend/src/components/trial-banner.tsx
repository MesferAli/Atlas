import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, Sparkles } from "lucide-react";
import { Link } from "wouter";
import { useTranslations } from "@/lib/i18n";

interface TenantInfo {
  id: string;
  name: string;
  status: string;
  companySize: string | null;
  trialEndsAt: string | null;
  onboardingCompleted: boolean;
}

export function TrialBanner() {
  const t = useTranslations();
  
  const { data: tenant, isLoading } = useQuery<TenantInfo>({
    queryKey: ["/api/tenant"],
  });

  if (isLoading || !tenant) {
    return null;
  }

  if (tenant.status !== "trial" && tenant.status !== "active") {
    return null;
  }

  if (!tenant.trialEndsAt) {
    return null;
  }

  const trialEndDate = new Date(tenant.trialEndsAt);
  const now = new Date();
  const diffTime = trialEndDate.getTime() - now.getTime();
  const daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (daysRemaining < 1 || daysRemaining > 7) {
    return null;
  }

  const isEnterprise = tenant.companySize === "enterprise";
  const trialLabel = isEnterprise 
    ? t.onboarding?.trialBanner?.enterpriseTrial 
    : t.onboarding?.trialBanner?.freeTrial;
  
  const daysLabel = daysRemaining === 1 
    ? t.onboarding?.trialBanner?.day 
    : t.onboarding?.trialBanner?.days;

  const getBannerColorClass = () => {
    if (daysRemaining === 1) {
      return "bg-destructive/10 text-destructive border-destructive/20";
    } else if (daysRemaining >= 2 && daysRemaining <= 4) {
      return "bg-chart-4/10 text-chart-4 border-chart-4/20";
    } else {
      return "bg-primary/10 text-primary border-primary/20";
    }
  };

  const getBadgeVariant = () => {
    if (daysRemaining === 1) {
      return "destructive" as const;
    } else if (daysRemaining >= 2 && daysRemaining <= 4) {
      return "secondary" as const;
    } else {
      return "default" as const;
    }
  };

  return (
    <div
      className={`flex items-center justify-center gap-3 px-4 py-2 border-b ${getBannerColorClass()}`}
      data-testid="banner-trial"
    >
      <Sparkles className="h-4 w-4 shrink-0" />
      <div className="flex items-center gap-2 flex-wrap justify-center">
        <Badge variant={getBadgeVariant()} className="text-xs" data-testid="badge-trial-status">
          {trialLabel}
        </Badge>
        <div className="flex items-center gap-1.5 text-sm font-medium">
          <Clock className="h-3.5 w-3.5" />
          <span data-testid="text-days-remaining">
            {daysRemaining} {daysLabel} {t.onboarding?.trialBanner?.daysRemaining}
          </span>
        </div>
      </div>
      {!isEnterprise && (
        <Link href="/subscription">
          <Button size="sm" variant="default" className="h-7 text-xs" data-testid="button-upgrade-now">
            {t.onboarding?.trialBanner?.upgradeNow}
          </Button>
        </Link>
      )}
    </div>
  );
}
