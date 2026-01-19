import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Lock, Calendar, Rocket, Crown, Check } from "lucide-react";
import { useTranslations } from "@/lib/i18n";

interface TrialExpiredScreenProps {
  companyType: 'enterprise' | 'smb';
  onScheduleMeeting?: () => void;
  onSelectPlan?: (planId: string) => void;
}

interface PlanInfo {
  id: string;
  name: string;
  nameAr: string;
  price: string;
  priceLabel: string;
  icon: typeof Rocket;
  features: string[];
  testId: string;
}

const plans: PlanInfo[] = [
  {
    id: 'pilot',
    name: 'Pilot',
    nameAr: 'التجريبية',
    price: '299',
    priceLabel: 'ر.س / شهرياً',
    icon: Rocket,
    features: [
      'موصل واحد',
      'حتى 1,000 عنصر',
      '3 مستخدمين',
      'توصيات الذكاء الاصطناعي الأساسية',
    ],
    testId: 'button-select-plan-pilot',
  },
  {
    id: 'business',
    name: 'Business',
    nameAr: 'الأعمال',
    price: '799',
    priceLabel: 'ر.س / شهرياً',
    icon: Crown,
    features: [
      '5 موصلات',
      'حتى 10,000 عنصر',
      '10 مستخدمين',
      'توصيات الذكاء الاصطناعي المتقدمة',
      'اكتشاف الحالات الشاذة',
      'سياسات الحوكمة',
    ],
    testId: 'button-select-plan-business',
  },
];

export function TrialExpiredScreen({ 
  companyType, 
  onScheduleMeeting, 
  onSelectPlan 
}: TrialExpiredScreenProps) {
  const t = useTranslations();

  const handleScheduleMeeting = () => {
    if (onScheduleMeeting) {
      onScheduleMeeting();
    } else {
      console.log('Schedule meeting clicked - Enterprise trial expired');
    }
  };

  const handleSelectPlan = (planId: string) => {
    if (onSelectPlan) {
      onSelectPlan(planId);
    } else {
      console.log(`Plan selected: ${planId} - SMB trial expired`);
    }
  };

  if (companyType === 'enterprise') {
    return (
      <div 
        className="min-h-screen flex items-center justify-center bg-background p-4"
        data-testid="screen-trial-expired"
      >
        <Card className="w-full max-w-lg text-center">
          <CardHeader className="space-y-4 pb-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <Lock className="h-8 w-8 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <CardTitle className="text-2xl">
                {t.onboarding?.trialExpired?.enterpriseTitle || 'انتهت التجربة المؤسسية'}
              </CardTitle>
              <CardDescription className="text-base">
                {t.onboarding?.trialExpired?.enterpriseSubtitle || 'لتفعيل المنصة وتشغيل حالات استخدام إضافية، نحتاج جلسة تحديد متطلبات قصيرة.'}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="pb-8">
            <Button 
              size="lg" 
              className="w-full gap-2"
              onClick={handleScheduleMeeting}
              data-testid="button-schedule-meeting"
            >
              <Calendar className="h-5 w-5" />
              {t.onboarding?.trialExpired?.scheduleMeeting || 'احجز اجتماع تحديد المتطلبات'}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center bg-background p-4"
      data-testid="screen-trial-expired"
    >
      <div className="w-full max-w-3xl space-y-8">
        <div className="text-center space-y-4">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <Lock className="h-8 w-8 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-semibold">
            {t.onboarding?.trialExpired?.smbTitle || 'انتهت تجربتك المجانية'}
          </h1>
          <p className="text-muted-foreground text-base">
            {t.onboarding?.trialExpired?.smbSubtitle || 'اختر الباقة المناسبة لك للاستمرار'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {plans.map((plan) => {
            const IconComponent = plan.icon;
            return (
              <Card key={plan.id} className="relative hover-elevate">
                <CardHeader className="text-center pb-4">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 mb-3">
                    <IconComponent className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-xl">{plan.nameAr}</CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-sm text-muted-foreground mr-1">{plan.priceLabel}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-primary shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className="w-full"
                    onClick={() => handleSelectPlan(plan.id)}
                    data-testid={plan.testId}
                  >
                    {t.onboarding?.trialExpired?.choosePlan || 'اختر الباقة'}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
