import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { I18nProvider } from "@/lib/i18n";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { EnvironmentBanner } from "@/components/environment-banner";
import { TrialBanner } from "@/components/trial-banner";
import { TrialExpiredScreen } from "@/components/trial-expired-screen";
import { useAuth } from "@/hooks/use-auth";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import Dashboard from "@/pages/dashboard";
import Connectors from "@/pages/connectors";
import Mappings from "@/pages/mappings";
import Recommendations from "@/pages/recommendations";
import Anomalies from "@/pages/anomalies";
import Capabilities from "@/pages/capabilities";
import Policies from "@/pages/policies";
import Audit from "@/pages/audit";
import Onboarding from "@/pages/onboarding";
import SettingsPage from "@/pages/settings";
import Help from "@/pages/help";
import NotFound from "@/pages/not-found";
import LoginPage from "@/pages/login";
import RegisterPage from "@/pages/register";
import ForgotPasswordPage from "@/pages/forgot-password";
import LandingPage from "@/pages/landing";
import AdminCustomers from "@/pages/admin/customers";
import SubscriptionPage from "@/pages/subscription";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/dashboard" component={Dashboard} />
      <Route path="/connectors" component={Connectors} />
      <Route path="/mappings" component={Mappings} />
      <Route path="/recommendations" component={Recommendations} />
      <Route path="/anomalies" component={Anomalies} />
      <Route path="/capabilities" component={Capabilities} />
      <Route path="/policies" component={Policies} />
      <Route path="/audit" component={Audit} />
      <Route path="/onboarding" component={Onboarding} />
      <Route path="/settings" component={SettingsPage} />
      <Route path="/subscription" component={SubscriptionPage} />
      <Route path="/admin/customers" component={AdminCustomers} />
      <Route path="/help" component={Help} />
      <Route component={NotFound} />
    </Switch>
  );
}

interface OnboardingStatus {
  onboardingCompleted: boolean;
  companySize: string | null;
  selectedUseCase: string | null;
  trialExpired?: boolean;
}

interface TenantInfo {
  id: string;
  name: string;
  status: string;
  companySize: string | null;
  trialEndsAt: string | null;
  onboardingCompleted: boolean;
}

function AuthenticatedApp() {
  const [location, navigate] = useLocation();
  const [showMeetingForm, setShowMeetingForm] = useState(false);
  
  const { data: onboardingStatus, isLoading: isOnboardingLoading, error: onboardingError } = useQuery<OnboardingStatus>({
    queryKey: ["/api/onboarding/status"],
    retry: 2,
    retryDelay: 500,
  });

  const { data: tenant, isLoading: isTenantLoading } = useQuery<TenantInfo>({
    queryKey: ["/api/tenant"],
    enabled: !!onboardingStatus?.onboardingCompleted,
  });

  const sidebarStyle = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "3.5rem",
  };

  useEffect(() => {
    if (onboardingStatus && !onboardingStatus.onboardingCompleted && location !== "/onboarding") {
      navigate("/onboarding");
    }
  }, [onboardingStatus, location, navigate]);

  if (isOnboardingLoading || isTenantLoading) {
    return <LoadingScreen />;
  }

  if (onboardingError || !onboardingStatus?.onboardingCompleted) {
    return <Onboarding />;
  }

  // Check if trial has expired
  const isTrialExpired = tenant?.status === "trial_expired" || (
    tenant?.trialEndsAt && new Date(tenant.trialEndsAt) < new Date()
  );

  if (isTrialExpired && tenant) {
    const companyType = tenant.companySize === "enterprise" ? "enterprise" : "smb";
    return (
      <TrialExpiredScreen 
        companyType={companyType}
        onScheduleMeeting={() => {
          // Navigate to meeting scheduling or show form
          window.open("https://calendly.com/atlas-enterprise", "_blank");
        }}
        onSelectPlan={(planId) => {
          // Navigate to subscription page with plan selection
          navigate(`/subscription?plan=${planId}`);
        }}
      />
    );
  }

  return (
    <SidebarProvider style={sidebarStyle as React.CSSProperties}>
      <div className="flex h-screen w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <EnvironmentBanner />
          <TrialBanner />
          <main className="flex-1 flex flex-col overflow-hidden">
            <Router />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

function UnauthenticatedRouter() {
  return (
    <Switch>
      <Route path="/" component={LandingPage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/register" component={RegisterPage} />
      <Route path="/forgot-password" component={ForgotPasswordPage} />
      <Route component={LandingPage} />
    </Switch>
  );
}

function AppContent() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <UnauthenticatedRouter />;
  }

  return <AuthenticatedApp />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <I18nProvider>
          <TooltipProvider>
            <AppContent />
            <Toaster />
          </TooltipProvider>
        </I18nProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
