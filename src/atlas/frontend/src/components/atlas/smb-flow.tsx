import { useAtlasFlow, type ToolType } from "@/lib/atlas-flow";
import { useI18n } from "@/lib/i18n";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Zap,
  Package,
  ShoppingCart,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Play,
  RefreshCw,
  Settings,
  Rocket,
  Crown,
  LayoutDashboard,
  Loader2,
  TrendingUp,
  AlertCircle,
  Sparkles
} from "lucide-react";
import { useState, useEffect } from "react";

const TOOL_OPTIONS: { id: ToolType; icon: typeof Package; labelKey: string }[] = [
  { id: "inventory", icon: Package, labelKey: "inventory" },
  { id: "orders", icon: ShoppingCart, labelKey: "orders" },
  { id: "analytics", icon: BarChart3, labelKey: "analytics" },
];

function EntryScreen() {
  const { nextStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.smb?.entry || {
    title: "ابدأ بسرعة",
    description: "أدوات ذكية للشركات الصغيرة والمتوسطة",
    cta: "ابدأ الآن",
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
            <Zap className="w-10 h-10 text-primary" />
          </div>
          <CardTitle className="text-3xl" data-testid="text-smb-entry-headline">
            {texts.title}
          </CardTitle>
          <CardDescription className="text-lg" data-testid="text-smb-entry-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <Button 
            onClick={nextStep} 
            className="w-full h-14 text-lg"
            data-testid="button-smb-entry-start"
          >
            {texts.cta}
            {isRTL ? <ArrowLeft className="w-5 h-5" /> : <ArrowRight className="w-5 h-5" />}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function SelectToolsScreen() {
  const { state, toggleTool, nextStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.smb?.selectTools || {
    title: "اختر أدواتك",
    description: "حدد ما تريد إدارته",
    cta: "متابعة",
    tools: {
      inventory: "المخزون",
      orders: "الطلبات",
      analytics: "التحليلات",
    },
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-smb-select-tools-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-smb-select-tools-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4">
            {TOOL_OPTIONS.map((tool) => {
              const Icon = tool.icon;
              const isSelected = state.selectedTools.includes(tool.id);
              return (
                <Button
                  key={tool.id}
                  variant="outline"
                  onClick={() => toggleTool(tool.id)}
                  className={`flex items-center justify-start gap-4 p-5 h-auto rounded-lg border-2 transition-colors ${
                    isSelected 
                      ? "border-primary bg-primary/5" 
                      : "border-border hover:border-primary/50"
                  }`}
                  data-testid={`button-smb-tool-${tool.id}`}
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="font-medium text-lg">
                    {texts.tools?.[tool.labelKey as keyof typeof texts.tools] || tool.labelKey}
                  </span>
                  {isSelected && (
                    <CheckCircle2 className={`w-6 h-6 text-primary ${isRTL ? 'mr-auto' : 'ml-auto'}`} />
                  )}
                </Button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={prevStep}
              className="h-14"
              data-testid="button-smb-select-tools-back"
            >
              {isRTL ? <ArrowRight className="w-5 h-5" /> : <ArrowLeft className="w-5 h-5" />}
            </Button>
            <Button 
              onClick={nextStep} 
              className="flex-1 h-14 text-lg"
              disabled={state.selectedTools.length === 0}
              data-testid="button-smb-select-tools-continue"
            >
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function InstantConnectScreen() {
  const { nextStep, prevStep, goToStep, setExecutionStatus } = useAtlasFlow();
  const { t, isRTL } = useI18n();
  const [isConnecting, setIsConnecting] = useState(false);

  const texts = t.atlas?.smb?.instantConnect || {
    title: "اتصال فوري",
    description: "ربط سريع بنقرة واحدة",
    cta: "اتصل الآن",
    connecting: "جاري الاتصال...",
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    const success = Math.random() > 0.2;
    if (success) {
      setExecutionStatus("success");
      nextStep();
    } else {
      setExecutionStatus("error");
      goToStep("error");
    }
    setIsConnecting(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
            {isConnecting ? (
              <Loader2 className="w-10 h-10 text-primary animate-spin" />
            ) : (
              <Rocket className="w-10 h-10 text-primary" />
            )}
          </div>
          <CardTitle className="text-2xl" data-testid="text-smb-instant-connect-headline">
            {texts.title}
          </CardTitle>
          <CardDescription className="text-base" data-testid="text-smb-instant-connect-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={handleConnect} 
            className="w-full h-14 text-lg"
            disabled={isConnecting}
            data-testid="button-smb-instant-connect"
          >
            {isConnecting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {texts.connecting}
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                {texts.cta}
              </>
            )}
          </Button>
          <Button 
            variant="ghost" 
            onClick={prevStep}
            className="w-full"
            disabled={isConnecting}
            data-testid="button-smb-instant-connect-back"
          >
            {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function ReadyScenarioScreen() {
  const { nextStep, prevStep, setSelectedUseCase } = useAtlasFlow();
  const { t, isRTL } = useI18n();
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);

  const texts = t.atlas?.smb?.readyScenario || {
    title: "سيناريوهات جاهزة",
    description: "اختر سيناريو معد مسبقاً",
    cta: "تشغيل",
    scenarios: {
      quickStart: "البدء السريع",
      salesBoost: "تعزيز المبيعات",
      inventoryOptimize: "تحسين المخزون",
    },
  };

  const scenarios = [
    { id: "quick-start", icon: Zap, label: texts.scenarios?.quickStart },
    { id: "sales-boost", icon: TrendingUp, label: texts.scenarios?.salesBoost },
    { id: "inventory", icon: Package, label: texts.scenarios?.inventoryOptimize },
  ];

  const handleContinue = () => {
    if (selectedScenario) {
      setSelectedUseCase(selectedScenario);
      nextStep();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-smb-ready-scenario-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-smb-ready-scenario-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-3">
            {scenarios.map((scenario) => {
              const Icon = scenario.icon;
              const isSelected = selectedScenario === scenario.id;
              return (
                <Button
                  key={scenario.id}
                  variant="outline"
                  onClick={() => setSelectedScenario(scenario.id)}
                  className={`flex items-center justify-start gap-4 p-4 h-auto rounded-lg border-2 transition-colors ${
                    isSelected 
                      ? "border-primary bg-primary/5" 
                      : "border-border hover:border-primary/50"
                  }`}
                  data-testid={`button-smb-scenario-${scenario.id}`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className={`flex-1 text-${isRTL ? 'right' : 'left'}`}>
                    <span className="font-medium block">{scenario.label}</span>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="w-5 h-5 text-primary" />
                  )}
                </Button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={prevStep}
              className="h-12"
              data-testid="button-smb-ready-scenario-back"
            >
              {isRTL ? <ArrowRight className="w-5 h-5" /> : <ArrowLeft className="w-5 h-5" />}
            </Button>
            <Button 
              onClick={handleContinue} 
              className="flex-1 h-12 text-lg"
              disabled={!selectedScenario}
              data-testid="button-smb-ready-scenario-run"
            >
              <Play className="w-5 h-5" />
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function RunResultScreen() {
  const { nextStep, goToStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  const texts = t.atlas?.smb?.runResult || {
    title: "النتائج",
    description: "إليك ما وجدناه",
    cta: "متابعة",
    analyzing: "جاري التحليل...",
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsComplete(true);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
    return () => clearInterval(interval);
  }, []);

  const demoStats = {
    items: 856,
    orders: 23,
    insights: 12,
  };

  const statsTexts = t.atlas?.smb?.dashboardLite?.stats || {
    items: "العناصر",
    orders: "الطلبات",
    insights: "الرؤى",
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
            {isComplete ? (
              <CheckCircle2 className="w-10 h-10 text-primary" />
            ) : (
              <Loader2 className="w-10 h-10 text-primary animate-spin" />
            )}
          </div>
          <CardTitle className="text-2xl" data-testid="text-smb-run-result-headline">
            {isComplete ? texts.title : texts.analyzing}
          </CardTitle>
          <CardDescription data-testid="text-smb-run-result-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!isComplete && (
            <Progress value={progress} className="h-3" data-testid="progress-smb-run-result" />
          )}

          {isComplete && (
            <div className="grid grid-cols-3 gap-4 bg-muted/50 rounded-lg p-4">
              <div>
                <p className="text-2xl font-bold">{demoStats.items.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">{statsTexts.items}</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-primary">{demoStats.orders}</p>
                <p className="text-xs text-muted-foreground">{statsTexts.orders}</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{demoStats.insights}</p>
                <p className="text-xs text-muted-foreground">{statsTexts.insights}</p>
              </div>
            </div>
          )}

          <Button 
            onClick={nextStep} 
            className="w-full h-14 text-lg"
            disabled={!isComplete}
            data-testid="button-smb-run-result-continue"
          >
            {texts.cta}
            {isRTL ? <ArrowLeft className="w-5 h-5" /> : <ArrowRight className="w-5 h-5" />}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function ErrorScreen() {
  const { state, goToStep, prevStep, setExecutionStatus } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.smb?.error || {
    title: "حدث خطأ",
    description: "لا تقلق، يمكنك المحاولة مرة أخرى",
    retry: "إعادة المحاولة",
  };

  const commonTexts = t.atlas?.common || {
    back: "رجوع",
  };

  const handleRetry = () => {
    setExecutionStatus("idle");
    goToStep("instant-connect");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertTriangle className="w-10 h-10 text-destructive" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-smb-error-headline">
            {texts.title}
          </CardTitle>
          <CardDescription className="text-base" data-testid="text-smb-error-description">
            {state.errorMessage || texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={handleRetry} 
            className="w-full h-14 text-lg"
            data-testid="button-smb-error-retry"
          >
            <RefreshCw className="w-5 h-5" />
            {texts.retry}
          </Button>
          <Button 
            variant="ghost" 
            onClick={prevStep}
            className="w-full"
            data-testid="button-smb-error-back"
          >
            {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            {commonTexts.back}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function ContinueScreen() {
  const { nextStep, goToStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.smb?.continue || {
    title: "ماذا تريد أن تفعل؟",
    description: "اختر الخطوة التالية",
    goToDashboard: "لوحة التحكم",
    modifySettings: "تعديل الإعدادات",
    upgrade: "ترقية",
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-smb-continue-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-smb-continue-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={() => goToStep("dashboard-lite")} 
            className="w-full h-14 text-lg"
            data-testid="button-smb-continue-dashboard"
          >
            <LayoutDashboard className="w-5 h-5" />
            {texts.goToDashboard}
          </Button>
          <Button 
            variant="outline"
            onClick={() => goToStep("select-tools")} 
            className="w-full h-14"
            data-testid="button-smb-continue-settings"
          >
            <Settings className="w-5 h-5" />
            {texts.modifySettings}
          </Button>
          <Button 
            variant="ghost"
            onClick={() => goToStep("upsell")} 
            className="w-full h-14"
            data-testid="button-smb-continue-upgrade"
          >
            <Crown className="w-5 h-5" />
            {texts.upgrade}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function UpsellScreen() {
  const { goToStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.smb?.upsell || {
    title: "اكتشف المزيد",
    description: "ميزات إضافية لتطوير أعمالك",
    cta: "ترقية الآن",
    laterCta: "لاحقاً",
    features: {
      unlimited: "موصلات غير محدودة",
      advanced: "تحليلات متقدمة",
      support: "دعم مخصص",
    },
  };

  const features = [
    { icon: Zap, label: texts.features?.unlimited },
    { icon: BarChart3, label: texts.features?.advanced },
    { icon: AlertCircle, label: texts.features?.support },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-amber-500/10 flex items-center justify-center">
            <Crown className="w-10 h-10 text-amber-500" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-smb-upsell-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-smb-upsell-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={index} 
                  className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
                >
                  <Icon className="w-5 h-5 text-primary" />
                  <span className="font-medium">{feature.label}</span>
                </div>
              );
            })}
          </div>

          <Button 
            onClick={() => window.location.href = "/subscription"} 
            className="w-full h-14 text-lg bg-amber-500 hover:bg-amber-600"
            data-testid="button-smb-upsell-upgrade"
          >
            <Crown className="w-5 h-5" />
            {texts.cta}
          </Button>
          <Button 
            variant="ghost"
            onClick={() => goToStep("dashboard-lite")}
            className="w-full"
            data-testid="button-smb-upsell-later"
          >
            {texts.laterCta}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function DashboardLiteScreen() {
  const { state, resetFlow } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.smb?.dashboardLite || {
    title: "لوحة التحكم",
    description: "نظرة سريعة على أعمالك",
    cta: "عرض التفاصيل",
    stats: {
      items: "العناصر",
      orders: "الطلبات",
      insights: "الرؤى",
    },
  };

  const dashboardTexts = t.dashboard || {
    healthy: "سليم",
  };

  const demoStats = {
    items: 856,
    orders: 23,
    insights: 5,
  };

  const handleGoToDashboard = () => {
    resetFlow();
    window.location.href = "/dashboard";
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-smb-dashboard-lite-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-smb-dashboard-lite-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-center gap-2">
            <Badge variant="secondary" className="gap-1" data-testid="badge-smb-status-healthy">
              <CheckCircle2 className="w-3 h-3" />
              {dashboardTexts.healthy}
            </Badge>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-3xl font-bold">{demoStats.items.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">{texts.stats?.items}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-3xl font-bold text-primary">{demoStats.orders}</p>
              <p className="text-xs text-muted-foreground">{texts.stats?.orders}</p>
            </div>
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-3xl font-bold">{demoStats.insights}</p>
              <p className="text-xs text-muted-foreground">{texts.stats?.insights}</p>
            </div>
          </div>

          <div className="border rounded-lg p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <span className="font-medium">{demoStats.insights} {texts.stats?.insights}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {state.selectedTools.includes("inventory") && <Package className="w-4 h-4" />} 
              {state.selectedTools.includes("orders") && <ShoppingCart className="w-4 h-4" />} 
              {state.selectedTools.includes("analytics") && <BarChart3 className="w-4 h-4" />}
            </div>
          </div>

          <Button 
            onClick={handleGoToDashboard} 
            className="w-full h-14 text-lg"
            data-testid="button-smb-dashboard-lite-continue"
          >
            <LayoutDashboard className="w-5 h-5" />
            {texts.cta}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

interface SMBFlowProps {
  onComplete?: () => void;
}

export function SMBFlow({ onComplete }: SMBFlowProps) {
  const { state, getProgress } = useAtlasFlow();
  const { isRTL } = useI18n();

  const renderScreen = () => {
    switch (state.currentStep) {
      case "entry":
        return <EntryScreen />;
      case "select-tools":
        return <SelectToolsScreen />;
      case "instant-connect":
        return <InstantConnectScreen />;
      case "ready-scenario":
        return <ReadyScenarioScreen />;
      case "run-result":
        return <RunResultScreen />;
      case "error":
        return <ErrorScreen />;
      case "continue":
        return <ContinueScreen />;
      case "upsell":
        return <UpsellScreen />;
      case "dashboard-lite":
        return <DashboardLiteScreen />;
      default:
        return <EntryScreen />;
    }
  };

  const progress = getProgress();
  const showProgress = !["error", "upsell", "dashboard-lite"].includes(state.currentStep);

  return (
    <div className={`min-h-screen bg-background ${isRTL ? 'rtl' : 'ltr'}`} dir={isRTL ? 'rtl' : 'ltr'}>
      {showProgress && progress > 0 && (
        <div className="fixed top-0 left-0 right-0 z-50">
          <Progress value={progress} className="h-1 rounded-none" data-testid="progress-smb-flow" />
        </div>
      )}
      {renderScreen()}
    </div>
  );
}

export default SMBFlow;
