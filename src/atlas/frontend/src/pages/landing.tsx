import { CircleDot, Plug, Sparkles, Shield, BarChart3, Package, Truck, Users, TrendingUp, Settings, ArrowRight, Check, Grid2X2 } from "lucide-react";
import { SiOracle, SiSap } from "react-icons/si";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/lib/i18n";
import { LanguageToggle } from "@/components/language-toggle";

export default function LandingPage() {
  const { t, language } = useI18n();
  const isRTL = language === "ar";

  const handleGetStarted = () => {
    window.location.href = "/register";
  };

  const handleSignIn = () => {
    window.location.href = "/login";
  };

  const pillars = [
    {
      icon: <Plug className="h-8 w-8" />,
      title: t.landing.pillars.connectors.title,
      description: t.landing.pillars.connectors.description,
      testId: "card-pillar-connectors",
    },
    {
      icon: <Sparkles className="h-8 w-8" />,
      title: t.landing.pillars.aiEngine.title,
      description: t.landing.pillars.aiEngine.description,
      testId: "card-pillar-ai",
    },
    {
      icon: <Shield className="h-8 w-8" />,
      title: t.landing.pillars.governance.title,
      description: t.landing.pillars.governance.description,
      testId: "card-pillar-governance",
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: t.landing.pillars.analytics.title,
      description: t.landing.pillars.analytics.description,
      testId: "card-pillar-analytics",
    },
  ];

  const useCases = [
    {
      icon: <Package className="h-6 w-6" />,
      title: t.landing.useCases.inventory.title,
      description: t.landing.useCases.inventory.description,
      testId: "card-usecase-inventory",
    },
    {
      icon: <Truck className="h-6 w-6" />,
      title: t.landing.useCases.supplyChain.title,
      description: t.landing.useCases.supplyChain.description,
      testId: "card-usecase-supplychain",
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: t.landing.useCases.hr.title,
      description: t.landing.useCases.hr.description,
      testId: "card-usecase-hr",
    },
    {
      icon: <TrendingUp className="h-6 w-6" />,
      title: t.landing.useCases.sales.title,
      description: t.landing.useCases.sales.description,
      testId: "card-usecase-sales",
    },
    {
      icon: <Settings className="h-6 w-6" />,
      title: t.landing.useCases.operations.title,
      description: t.landing.useCases.operations.description,
      testId: "card-usecase-operations",
    },
  ];

  const pricingPlans = [
    {
      name: t.landing.pricing.basic.name,
      price: t.landing.pricing.basic.price,
      currency: t.landing.pricing.basic.currency,
      features: t.landing.pricing.basic.features,
      popular: false,
      testId: "card-pricing-basic",
    },
    {
      name: t.landing.pricing.professional.name,
      price: t.landing.pricing.professional.price,
      currency: t.landing.pricing.professional.currency,
      features: t.landing.pricing.professional.features,
      popular: true,
      testId: "card-pricing-professional",
    },
    {
      name: t.landing.pricing.enterprise.name,
      price: t.landing.pricing.enterprise.price,
      currency: t.landing.pricing.enterprise.currency,
      features: t.landing.pricing.enterprise.features,
      popular: false,
      testId: "card-pricing-enterprise",
    },
  ];

  return (
    <div className="min-h-screen bg-background" dir={isRTL ? "rtl" : "ltr"}>
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <CircleDot className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">{t.brand.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <LanguageToggle />
            <Button
              variant="ghost"
              onClick={handleSignIn}
              data-testid="button-header-signin"
            >
              {t.landing.hero.signIn}
            </Button>
            <Button
              onClick={handleGetStarted}
              data-testid="button-header-getstarted"
            >
              {t.landing.hero.getStarted}
            </Button>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent/10" />
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 20% 50%, hsl(var(--primary) / 0.08) 0%, transparent 50%),
                           radial-gradient(circle at 80% 80%, hsl(var(--accent) / 0.1) 0%, transparent 50%),
                           radial-gradient(circle at 40% 20%, hsl(var(--primary) / 0.05) 0%, transparent 30%)`
        }} />
        
        <div className="container mx-auto px-4 py-24 md:py-32 relative">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <div className="flex items-center justify-center gap-3 mb-6">
              <CircleDot className="h-20 w-20 text-primary opacity-80" />
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-light tracking-tight" data-testid="text-hero-title">
              {t.landing.hero.title}
            </h1>
            
            <p className="text-xl md:text-2xl text-muted-foreground" data-testid="text-hero-subtitle">
              {t.landing.hero.subtitle}
            </p>
            
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto" data-testid="text-hero-description">
              {t.landing.hero.description}
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Button
                size="lg"
                className="gap-2 min-w-[180px]"
                onClick={handleGetStarted}
                data-testid="button-hero-getstarted"
              >
                {t.landing.hero.getStarted}
                <ArrowRight className={`h-4 w-4 ${isRTL ? "rotate-180" : ""}`} />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="min-w-[180px]"
                onClick={handleSignIn}
                data-testid="button-hero-signin"
              >
                {t.landing.hero.signIn}
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 border-b bg-muted/20">
        <div className="container mx-auto px-4">
          <p className="text-center text-sm text-muted-foreground mb-8 uppercase tracking-wide" data-testid="text-partners-title">
            {t.landing.partners.title}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16">
            <div className="flex items-center gap-2 text-muted-foreground/60" data-testid="partner-oracle">
              <SiOracle className="h-8 w-8" />
              <span className="text-lg font-medium">{t.landing.partners.oracle}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground/60" data-testid="partner-sap">
              <SiSap className="h-8 w-8" />
              <span className="text-lg font-medium">{t.landing.partners.sap}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground/60" data-testid="partner-zoho">
              <span className="text-2xl font-bold">Z</span>
              <span className="text-lg font-medium">{t.landing.partners.zoho}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground/60" data-testid="partner-microsoft">
              <Grid2X2 className="h-7 w-7" />
              <span className="text-lg font-medium">{t.landing.partners.microsoft}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 md:py-28">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-medium mb-4" data-testid="text-pillars-title">
              {t.landing.pillars.title}
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto" data-testid="text-pillars-subtitle">
              {t.landing.pillars.subtitle}
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {pillars.map((pillar) => (
              <Card 
                key={pillar.testId} 
                className="text-center hover-elevate transition-all" 
                data-testid={pillar.testId}
              >
                <CardContent className="pt-6 space-y-4">
                  <div className="mx-auto w-16 h-16 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    {pillar.icon}
                  </div>
                  <h3 className="text-lg font-medium">{pillar.title}</h3>
                  <p className="text-muted-foreground text-sm">{pillar.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 md:py-28 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-medium mb-4" data-testid="text-usecases-title">
              {t.landing.useCases.title}
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto" data-testid="text-usecases-subtitle">
              {t.landing.useCases.subtitle}
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {useCases.map((useCase) => (
              <Card 
                key={useCase.testId} 
                className="hover-elevate transition-all" 
                data-testid={useCase.testId}
              >
                <CardContent className="pt-6 space-y-3">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                    {useCase.icon}
                  </div>
                  <h3 className="font-medium">{useCase.title}</h3>
                  <p className="text-muted-foreground text-sm">{useCase.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 md:py-28">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-medium mb-4" data-testid="text-pricing-title">
              {t.landing.pricing.title}
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto" data-testid="text-pricing-subtitle">
              {t.landing.pricing.subtitle}
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {pricingPlans.map((plan) => (
              <Card 
                key={plan.testId} 
                className={`relative hover-elevate transition-all ${plan.popular ? "border-primary border-2" : ""}`}
                data-testid={plan.testId}
              >
                {plan.popular && (
                  <Badge 
                    className="absolute -top-3 left-1/2 -translate-x-1/2"
                    data-testid="badge-most-popular"
                  >
                    {t.landing.pricing.mostPopular}
                  </Badge>
                )}
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-light">{plan.price}</span>
                    <span className="text-lg text-muted-foreground ms-1">{plan.currency}</span>
                    <span className="text-muted-foreground">{t.landing.pricing.perMonth}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <ul className="space-y-3">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full"
                    variant={plan.popular ? "default" : "outline"}
                    onClick={handleGetStarted}
                    data-testid={`button-pricing-${plan.testId.split('-').pop()}`}
                  >
                    {plan.name === t.landing.pricing.enterprise.name 
                      ? t.landing.pricing.contactSales 
                      : t.landing.pricing.startFreeTrial}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 md:py-28 bg-primary/5">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <h2 className="text-3xl md:text-4xl font-medium" data-testid="text-cta-title">
              {t.landing.cta.title}
            </h2>
            <p className="text-lg text-muted-foreground" data-testid="text-cta-subtitle">
              {t.landing.cta.subtitle}
            </p>
            <Button
              size="lg"
              className="gap-2"
              onClick={handleGetStarted}
              data-testid="button-cta-getstarted"
            >
              {t.landing.cta.button}
              <ArrowRight className={`h-4 w-4 ${isRTL ? "rotate-180" : ""}`} />
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t py-12 md:py-16">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div>
              <h3 className="font-medium mb-4 text-sm uppercase tracking-wide text-muted-foreground">
                {t.landing.footer.product}
              </h3>
              <ul className="space-y-3">
                <li>
                  <a href="#pillars" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-pillars">
                    {t.landing.pillars.title}
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-pricing">
                    {t.landing.pricing.title}
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-4 text-sm uppercase tracking-wide text-muted-foreground">
                {t.landing.footer.company}
              </h3>
              <ul className="space-y-3">
                <li>
                  <a href="#about" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-about">
                    {t.landing.footer.about}
                  </a>
                </li>
                <li>
                  <a href="#careers" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-careers">
                    {t.landing.footer.careers}
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-4 text-sm uppercase tracking-wide text-muted-foreground">
                {t.landing.footer.resources}
              </h3>
              <ul className="space-y-3">
                <li>
                  <a href="#blog" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-blog">
                    {t.landing.footer.blog}
                  </a>
                </li>
                <li>
                  <a href="#docs" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-docs">
                    {t.landing.footer.docs}
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-4 text-sm uppercase tracking-wide text-muted-foreground">
                {t.landing.footer.legal}
              </h3>
              <ul className="space-y-3">
                <li>
                  <a href="#privacy" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-privacy">
                    {t.landing.footer.privacy}
                  </a>
                </li>
                <li>
                  <a href="#terms" className="text-sm text-foreground/80 hover:text-primary" data-testid="link-footer-terms">
                    {t.landing.footer.terms}
                  </a>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="border-t pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <CircleDot className="h-6 w-6 text-primary" />
              <span className="font-medium">{t.brand.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} {t.brand.name}. {t.landing.footer.copyright}.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
