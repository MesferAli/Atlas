import { useAtlasFlow, type SystemType, type AccessType } from "@/lib/atlas-flow";
import { useI18n } from "@/lib/i18n";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Building2, 
  Server, 
  Key, 
  Shield, 
  Database,
  Play,
  CheckCircle2,
  AlertTriangle,
  Rocket,
  ArrowLeft,
  ArrowRight,
  Box,
  RefreshCw,
  Eye,
  Zap,
  Settings2,
  Lock,
  Unlock,
  FileCheck,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { useState, useEffect } from "react";

const SYSTEM_OPTIONS: { id: SystemType; icon: typeof Server; labelKey: string }[] = [
  { id: "sap", icon: Server, labelKey: "sap" },
  { id: "oracle", icon: Database, labelKey: "oracle" },
  { id: "dynamics", icon: Settings2, labelKey: "dynamics" },
  { id: "custom-rest", icon: Zap, labelKey: "customRest" },
  { id: "demo", icon: Play, labelKey: "demo" },
];

const ACCESS_OPTIONS: { id: AccessType; icon: typeof Key; labelKey: string }[] = [
  { id: "api-key", icon: Key, labelKey: "apiKey" },
  { id: "bearer-token", icon: Lock, labelKey: "bearerToken" },
  { id: "oauth2", icon: Shield, labelKey: "oauth2" },
];

function EntryScreen() {
  const { nextStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.entry || {
    title: "مرحباً بك في Atlas للمؤسسات",
    description: "منصة الذكاء الاصطناعي المؤسسي لربط أنظمتك والحصول على توصيات ذكية",
    cta: "ابدأ الإعداد",
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg text-center">
        <CardHeader className="space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Building2 className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-entry-headline">
            {texts.title}
          </CardTitle>
          <CardDescription className="text-base" data-testid="text-entry-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Button 
            onClick={nextStep} 
            className="w-full h-10"
            data-testid="button-entry-start"
          >
            {texts.cta}
            {isRTL ? <ArrowLeft className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function SelectSystemScreen() {
  const { state, setSelectedSystem, nextStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.selectSystem || {
    title: "اختر النظام الذي تريد ربطه",
    description: "حدد نظام ERP أو REST API الذي تريد الاتصال به",
    cta: "متابعة",
    systems: {
      sap: "SAP ERP",
      oracle: "Oracle EBS",
      dynamics: "Microsoft Dynamics",
      customRest: "REST API مخصص",
      demo: "بيانات تجريبية",
    },
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-select-system-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-select-system-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-3">
            {SYSTEM_OPTIONS.map((system) => {
              const Icon = system.icon;
              const isSelected = state.selectedSystem === system.id;
              return (
                <Button
                  key={system.id}
                  variant="outline"
                  onClick={() => setSelectedSystem(system.id)}
                  className={`flex items-center justify-start gap-4 p-4 h-auto rounded-lg transition-colors ${
                    isSelected 
                      ? "border-primary bg-primary/5" 
                      : "border-border hover:border-primary/50"
                  }`}
                  data-testid={`button-system-${system.id}`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="font-medium">
                    {texts.systems?.[system.labelKey as keyof typeof texts.systems] || system.labelKey}
                  </span>
                  {isSelected && (
                    <CheckCircle2 className={`w-5 h-5 text-primary ${isRTL ? 'mr-auto' : 'ml-auto'}`} />
                  )}
                </Button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={prevStep}
              data-testid="button-select-system-back"
            >
              {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            </Button>
            <Button 
              onClick={nextStep} 
              className="flex-1 h-10"
              disabled={!state.selectedSystem}
              data-testid="button-select-system-continue"
            >
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AccessTypeScreen() {
  const { state, setAccessType, nextStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.accessType || {
    title: "اختر طريقة المصادقة",
    description: "حدد كيفية الاتصال بالنظام",
    cta: "متابعة",
    types: {
      apiKey: "مفتاح API",
      bearerToken: "رمز Bearer",
      oauth2: "OAuth 2.0",
      basicAuth: "المصادقة الأساسية",
    },
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-access-type-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-access-type-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-3">
            {ACCESS_OPTIONS.map((access) => {
              const Icon = access.icon;
              const isSelected = state.accessType === access.id;
              return (
                <Button
                  key={access.id}
                  variant="outline"
                  onClick={() => setAccessType(access.id)}
                  className={`flex items-center justify-start gap-4 p-4 h-auto rounded-lg transition-colors ${
                    isSelected 
                      ? "border-primary bg-primary/5" 
                      : "border-border hover:border-primary/50"
                  }`}
                  data-testid={`button-access-${access.id}`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className={`text-${isRTL ? 'right' : 'left'}`}>
                    <span className="font-medium block">
                      {texts.types?.[access.labelKey as keyof typeof texts.types] || access.labelKey}
                    </span>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className={`w-5 h-5 text-primary ${isRTL ? 'mr-auto' : 'ml-auto'}`} />
                  )}
                </Button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={prevStep}
              data-testid="button-access-type-back"
            >
              {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            </Button>
            <Button 
              onClick={nextStep} 
              className="flex-1 h-10"
              disabled={!state.accessType}
              data-testid="button-access-type-continue"
            >
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SandboxScreen() {
  const { state, setSandboxEnabled, nextStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.sandbox || {
    title: "البيئة التجريبية",
    description: "جرب المنصة مع بيانات تجريبية قبل الإنتاج",
    cta: "جرب الآن",
    enableSandbox: "تفعيل البيئة التجريبية",
    demoData: {
      items: "منتجات",
      categories: "فئات",
      locations: "مواقع",
    },
  };

  const demoData = {
    items: 1250,
    categories: 45,
    locations: 12,
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-sandbox-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-sandbox-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setSandboxEnabled(true)}
              className={`flex-1 flex-col p-4 h-auto rounded-lg transition-colors ${
                state.sandboxEnabled 
                  ? "border-primary bg-primary/5" 
                  : "border-border"
              }`}
              data-testid="button-sandbox-enable"
            >
              <Box className="w-8 h-8 mb-2 text-primary" />
              <span className="font-medium">{texts.enableSandbox}</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => setSandboxEnabled(false)}
              className={`flex-1 flex-col p-4 h-auto rounded-lg transition-colors ${
                !state.sandboxEnabled 
                  ? "border-primary bg-primary/5" 
                  : "border-border"
              }`}
              data-testid="button-sandbox-disable"
            >
              <Rocket className="w-8 h-8 mb-2 text-muted-foreground" />
              <span className="font-medium">{t.atlas?.enterprise?.preview?.production || "إنتاج"}</span>
            </Button>
          </div>

          {state.sandboxEnabled && (
            <div className="bg-muted/50 rounded-lg p-4 space-y-3">
              <p className="text-sm font-medium flex items-center gap-2">
                <Eye className="w-4 h-4" />
                {texts.description}
              </p>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-semibold">{demoData.items.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">{texts.demoData?.items}</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{demoData.categories}</p>
                  <p className="text-xs text-muted-foreground">{texts.demoData?.categories}</p>
                </div>
                <div>
                  <p className="text-2xl font-semibold">{demoData.locations}</p>
                  <p className="text-xs text-muted-foreground">{texts.demoData?.locations}</p>
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={prevStep}
              data-testid="button-sandbox-back"
            >
              {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            </Button>
            <Button 
              onClick={nextStep} 
              className="flex-1 h-10"
              data-testid="button-sandbox-continue"
            >
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SelectUseCaseScreen() {
  const { state, setSelectedUseCase, nextStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.selectUseCase || {
    title: "اختر حالة الاستخدام",
    description: "ما الذي تريد تحقيقه؟",
    cta: "متابعة",
    useCases: {
      inventory: "إدارة المخزون",
      supplyChain: "سلسلة التوريد",
      demand: "التنبؤ بالطلب",
    },
  };

  const useCases = [
    { 
      id: "inventory", 
      icon: Box, 
      label: texts.useCases?.inventory || "إدارة المخزون",
      description: t.onboarding?.useCase?.inventoryDesc || "تحسين مستويات المخزون وإعادة الطلب الذكية",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-use-case-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-use-case-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-3">
            {useCases.map((useCase) => {
              const Icon = useCase.icon;
              const isSelected = state.selectedUseCase === useCase.id;
              return (
                <Button
                  key={useCase.id}
                  variant="outline"
                  onClick={() => setSelectedUseCase(useCase.id)}
                  className={`flex items-center justify-start gap-4 p-4 h-auto rounded-lg transition-colors ${
                    isSelected 
                      ? "border-primary bg-primary/5" 
                      : "border-border hover:border-primary/50"
                  }`}
                  data-testid={`button-use-case-${useCase.id}`}
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    isSelected ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className={`flex-1 text-${isRTL ? 'right' : 'left'}`}>
                    <span className="font-medium block">{useCase.label}</span>
                    <span className="text-sm text-muted-foreground">{useCase.description}</span>
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
              data-testid="button-use-case-back"
            >
              {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            </Button>
            <Button 
              onClick={nextStep} 
              className="flex-1 h-10"
              disabled={!state.selectedUseCase}
              data-testid="button-use-case-continue"
            >
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PreviewScreen() {
  const { state, nextStep, prevStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.preview || {
    title: "مراجعة الإعداد",
    description: "تأكد من صحة الإعدادات قبل المتابعة",
    cta: "بدء التنفيذ",
    configuration: "الإعدادات",
    system: "النظام",
    accessType: "نوع المصادقة",
    useCase: "حالة الاستخدام",
    environment: "البيئة",
    sandbox: "تجريبية",
    production: "إنتاج",
  };

  const systemLabels: Record<string, string> = {
    sap: "SAP",
    oracle: "Oracle",
    dynamics: "Microsoft Dynamics",
    "custom-rest": "REST API مخصص",
    demo: "وضع تجريبي",
  };

  const accessLabels: Record<string, string> = {
    "api-key": "مفتاح API",
    "bearer-token": "رمز Bearer",
    oauth2: "OAuth 2.0",
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-2">
          <CardTitle className="text-2xl" data-testid="text-preview-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-preview-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-muted/50 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{texts.system}</span>
              <Badge variant="secondary" data-testid="badge-preview-system">
                {systemLabels[state.selectedSystem || ""] || state.selectedSystem}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{texts.accessType}</span>
              <Badge variant="secondary" data-testid="badge-preview-access">
                {accessLabels[state.accessType || ""] || state.accessType}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{texts.useCase}</span>
              <Badge variant="secondary" data-testid="badge-preview-use-case">
                {state.selectedUseCase === "inventory" ? "إدارة المخزون" : state.selectedUseCase}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{texts.environment}</span>
              <Badge 
                variant={state.sandboxEnabled ? "outline" : "default"}
                data-testid="badge-preview-environment"
              >
                {state.sandboxEnabled ? texts.sandbox : texts.production}
              </Badge>
            </div>
          </div>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={prevStep}
              data-testid="button-preview-back"
            >
              {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
            </Button>
            <Button 
              onClick={nextStep} 
              className="flex-1 h-10"
              data-testid="button-preview-execute"
            >
              <Play className="w-4 h-4" />
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ExecutionScreen() {
  const { state, setExecutionStatus, nextStep, goToStep } = useAtlasFlow();
  const { t } = useI18n();
  const [progress, setProgress] = useState(0);

  const texts = t.atlas?.enterprise?.execution || {
    title: "جاري التنفيذ...",
    description: "يتم الآن الاتصال بالنظام ومزامنة البيانات",
    steps: {
      connecting: "جاري الاتصال...",
      authenticating: "جاري المصادقة...",
      syncing: "جاري المزامنة...",
      analyzing: "جاري التحليل...",
      complete: "اكتمل",
    },
  };

  const steps = [
    { key: "connecting", threshold: 25 },
    { key: "authenticating", threshold: 50 },
    { key: "syncing", threshold: 75 },
    { key: "analyzing", threshold: 95 },
    { key: "complete", threshold: 100 },
  ];

  useEffect(() => {
    if (state.executionStatus !== "running") {
      setExecutionStatus("running");
    }

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setExecutionStatus("success");
          setTimeout(() => nextStep(), 500);
          return 100;
        }
        return prev + 2;
      });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const currentStep = steps.find((s) => progress <= s.threshold) || steps[steps.length - 1];

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
            <RefreshCw className="w-8 h-8 text-primary animate-spin" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-execution-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-execution-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Progress value={progress} className="h-2" data-testid="progress-execution" />
            <p className="text-sm text-center text-muted-foreground">
              {progress}%
            </p>
          </div>

          <div className="space-y-2">
            {steps.map((step) => {
              const isActive = currentStep.key === step.key;
              const isComplete = progress > step.threshold;
              return (
                <div 
                  key={step.key}
                  className={`flex items-center gap-3 p-2 rounded ${
                    isActive ? "bg-primary/5" : ""
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle2 className="w-5 h-5 text-primary" />
                  ) : isActive ? (
                    <RefreshCw className="w-5 h-5 text-primary animate-spin" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-muted" />
                  )}
                  <span className={isActive ? "font-medium" : "text-muted-foreground"}>
                    {texts.steps?.[step.key as keyof typeof texts.steps] || step.key}
                  </span>
                </div>
              );
            })}
          </div>

        </CardContent>
      </Card>
    </div>
  );
}

interface SuccessScreenProps {
  onComplete?: () => void;
}

function SuccessScreen({ onComplete }: SuccessScreenProps) {
  const { state, nextStep, goToStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.success || {
    title: "تم الإعداد بنجاح!",
    description: "تم ربط النظام وبدء تحليل البيانات",
    cta: "عرض لوحة التحكم",
    stats: {
      itemsSynced: "عناصر مزامنة",
      recommendations: "توصيات",
      confidenceScore: "درجة الثقة",
    },
  };
  
  const activateProductionTexts = t.atlas?.enterprise?.activateProduction || {
    title: "تفعيل الإنتاج",
  };

  const stats = {
    itemsSynced: 1250,
    recommendations: 8,
    confidence: 94,
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-success-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-success-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-3 gap-4 text-center bg-muted/50 rounded-lg p-4">
            <div>
              <p className="text-2xl font-semibold" data-testid="text-success-items">
                {stats.itemsSynced.toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">{texts.stats?.itemsSynced}</p>
            </div>
            <div>
              <p className="text-2xl font-semibold" data-testid="text-success-recommendations">
                {stats.recommendations}
              </p>
              <p className="text-xs text-muted-foreground">{texts.stats?.recommendations}</p>
            </div>
            <div>
              <p className="text-2xl font-semibold" data-testid="text-success-confidence">
                {stats.confidence}%
              </p>
              <p className="text-xs text-muted-foreground">{texts.stats?.confidenceScore}</p>
            </div>
          </div>

          <div className="space-y-3">
            <Button 
              className="w-full h-10"
              onClick={onComplete}
              data-testid="button-success-dashboard"
            >
              {texts.cta}
              {isRTL ? <ArrowLeft className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
            </Button>
            
            {state.sandboxEnabled && (
              <Button 
                variant="outline"
                className="w-full h-10"
                onClick={() => goToStep("activate-production")}
                data-testid="button-success-activate-production"
              >
                <Rocket className="w-4 h-4" />
                {activateProductionTexts.title}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ErrorScreen() {
  const { state, prevStep, goToStep, resetFlow } = useAtlasFlow();
  const { t, isRTL } = useI18n();

  const texts = t.atlas?.enterprise?.error || {
    title: "حدث خطأ",
    description: "فشل الاتصال بالنظام",
    retry: "إعادة المحاولة",
    goBack: "رجوع",
    startOver: "البدء من جديد",
    contactSupport: "تواصل مع الدعم",
  };

  const errorMessage = state.errorMessage || "خطأ في الاتصال بالنظام الخارجي";

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-destructive" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-error-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-error-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-4">
            <p className="text-sm text-muted-foreground" data-testid="text-error-message">
              {errorMessage}
            </p>
          </div>

          <div className="space-y-3">
            <Button 
              className="w-full h-10"
              onClick={() => goToStep("execution")}
              data-testid="button-error-retry"
            >
              <RefreshCw className="w-4 h-4" />
              {texts.retry}
            </Button>
            
            <div className="flex gap-3">
              <Button 
                variant="outline"
                className="flex-1"
                onClick={prevStep}
                data-testid="button-error-back"
              >
                {isRTL ? <ArrowRight className="w-4 h-4" /> : <ArrowLeft className="w-4 h-4" />}
                {texts.goBack}
              </Button>
              <Button 
                variant="outline"
                className="flex-1"
                onClick={resetFlow}
                data-testid="button-error-start-over"
              >
                {texts.startOver}
              </Button>
            </div>

            <Button 
              variant="ghost"
              className="w-full"
              data-testid="button-error-support"
            >
              {texts.contactSupport}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ActivateProductionScreenProps {
  onComplete?: () => void;
}

function ActivateProductionScreen({ onComplete }: ActivateProductionScreenProps) {
  const { state, setProductionReady, setSandboxEnabled, goToStep } = useAtlasFlow();
  const { t, isRTL } = useI18n();
  const [confirmed, setConfirmed] = useState(false);

  const commonTexts = t.atlas?.common || {
    cancel: "إلغاء",
  };

  const texts = t.atlas?.enterprise?.activateProduction || {
    title: "تفعيل الإنتاج",
    description: "انقل من البيئة التجريبية إلى الإنتاج",
    cta: "تفعيل الإنتاج",
    warning: "تحذير: سيتم تطبيق التغييرات على البيانات الحقيقية",
    checklist: {
      dataReviewed: "تمت مراجعة البيانات",
      settingsConfirmed: "تم تأكيد الإعدادات",
      teamNotified: "تم إبلاغ الفريق",
    },
    confirmProduction: "أؤكد أنني مستعد للإنتاج",
  };

  const handleActivate = () => {
    setProductionReady(true);
    setSandboxEnabled(false);
    if (onComplete) {
      onComplete();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Rocket className="w-8 h-8 text-primary" />
          </div>
          <CardTitle className="text-2xl" data-testid="text-activate-headline">
            {texts.title}
          </CardTitle>
          <CardDescription data-testid="text-activate-description">
            {texts.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <p className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              {texts.warning}
            </p>
          </div>

          <div className="bg-muted/50 rounded-lg p-4">
            <ul className="text-sm space-y-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                {texts.checklist?.dataReviewed}
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                {texts.checklist?.settingsConfirmed}
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                {texts.checklist?.teamNotified}
              </li>
            </ul>
          </div>

          <label className="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover-elevate">
            <input 
              type="checkbox" 
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-1"
              data-testid="checkbox-activate-confirm"
            />
            <span className="text-sm">{texts.confirmProduction}</span>
          </label>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => goToStep("success")}
              data-testid="button-activate-cancel"
            >
              {commonTexts.cancel}
            </Button>
            <Button 
              onClick={handleActivate} 
              className="flex-1 h-10"
              disabled={!confirmed}
              data-testid="button-activate-production"
            >
              <Unlock className="w-4 h-4" />
              {texts.cta}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface EnterpriseFlowProps {
  onComplete?: () => void;
}

export function EnterpriseFlow({ onComplete }: EnterpriseFlowProps) {
  const { state, getProgress } = useAtlasFlow();
  const { t } = useI18n();

  const texts = t.atlas?.enterprise?.entry || {
    title: "مرحباً بك في Atlas للمؤسسات",
  };

  const renderScreen = () => {
    switch (state.currentStep) {
      case "entry":
        return <EntryScreen />;
      case "select-system":
        return <SelectSystemScreen />;
      case "access-type":
        return <AccessTypeScreen />;
      case "sandbox":
        return <SandboxScreen />;
      case "select-use-case":
        return <SelectUseCaseScreen />;
      case "preview":
        return <PreviewScreen />;
      case "execution":
        return <ExecutionScreen />;
      case "success":
        return <SuccessScreen onComplete={onComplete} />;
      case "error":
        return <ErrorScreen />;
      case "activate-production":
        return <ActivateProductionScreen onComplete={onComplete} />;
      default:
        return <EntryScreen />;
    }
  };

  const progress = getProgress();

  return (
    <div className="min-h-screen bg-background">
      <div className="sticky top-0 z-10 bg-background border-b">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-lg font-medium" data-testid="text-flow-title">
              {texts.title}
            </h1>
            <Badge variant="outline" data-testid="badge-flow-progress">
              {Math.round(progress)}%
            </Badge>
          </div>
          <Progress value={progress} className="h-1" data-testid="progress-flow" />
        </div>
      </div>
      
      <main className="max-w-3xl mx-auto">
        {renderScreen()}
      </main>
    </div>
  );
}

export {
  EntryScreen,
  SelectSystemScreen,
  AccessTypeScreen,
  SandboxScreen,
  SelectUseCaseScreen,
  PreviewScreen,
  ExecutionScreen,
  SuccessScreen,
  ErrorScreen,
  ActivateProductionScreen,
};
