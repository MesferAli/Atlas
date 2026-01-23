import { useState, useEffect } from "react";
import { CircleDot, Mail, Lock, ArrowLeft, ArrowRight, Loader2, Zap, Shield, BarChart3, Users } from "lucide-react";
import { SiGoogle } from "react-icons/si";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/lib/i18n";
import { LanguageToggle } from "@/components/language-toggle";
import { Link } from "wouter";
import { motion } from "framer-motion";

function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);
    
    const handler = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };
    
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);
  
  return prefersReducedMotion;
}

export default function LoginPage() {
  const { t, language } = useI18n();
  const prefersReducedMotion = useReducedMotion();
  const isRTL = language === "ar";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const fadeInUp = {
    initial: prefersReducedMotion ? {} : { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: prefersReducedMotion ? 0 : 0.15 }
  };

  const staggerContainer = {
    animate: {
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.08
      }
    }
  };

  const [error, setError] = useState("");

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError("");
    
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        window.location.href = "/";
      } else {
        setError(data.message || t.auth.loginFailed);
      }
    } catch {
      setError(t.auth.connectionError);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    setIsLoading(true);
    window.location.href = "/api/auth/google";
  };

  const ArrowIcon = isRTL ? ArrowRight : ArrowLeft;

  const features = [
    {
      icon: Zap,
      title: isRTL ? "موصلات REST ذكية" : "Smart REST Connectors",
      description: isRTL ? "اتصال تلقائي بأي نظام عبر API" : "Auto-connect to any system via API"
    },
    {
      icon: BarChart3,
      title: isRTL ? "توصيات الذكاء الاصطناعي" : "AI Recommendations",
      description: isRTL ? "تنبؤات دقيقة بالطلب والمخزون" : "Accurate demand & inventory predictions"
    },
    {
      icon: Users,
      title: isRTL ? "موافقة بشرية" : "Human Approval",
      description: isRTL ? "كل قرار يتطلب موافقة صريحة" : "Every decision requires explicit approval"
    },
    {
      icon: Shield,
      title: isRTL ? "أمان مؤسسي" : "Enterprise Security",
      description: isRTL ? "عزل كامل وسجل تدقيق غير قابل للتغيير" : "Full isolation & immutable audit trail"
    }
  ];

  return (
    <div 
      className="min-h-screen flex"
      dir={isRTL ? "rtl" : "ltr"}
    >
      <div 
        className="hidden lg:flex lg:w-1/2 relative overflow-hidden"
        style={{ 
          background: "linear-gradient(135deg, hsl(192 45% 12%) 0%, hsl(192 45% 22%) 50%, hsl(192 45% 15%) 100%)"
        }}
      >
        <div className="absolute inset-0 opacity-30">
          <div 
            className="absolute top-20 left-20 w-64 h-64 rounded-full blur-3xl"
            style={{ backgroundColor: "hsl(192 45% 42% / 0.3)" }}
          />
          <div 
            className="absolute bottom-40 right-20 w-96 h-96 rounded-full blur-3xl"
            style={{ backgroundColor: "hsl(192 45% 42% / 0.2)" }}
          />
          <div 
            className="absolute top-1/2 left-1/3 w-48 h-48 rounded-full blur-2xl"
            style={{ backgroundColor: "hsl(192 45% 50% / 0.15)" }}
          />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20 w-full">
          <motion.div 
            initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
            className="mb-12"
          >
            <div className="flex items-center gap-3 mb-4">
              <div 
                className="p-3 rounded-xl"
                style={{ backgroundColor: "hsl(192 45% 42% / 0.2)" }}
              >
                <CircleDot 
                  className="h-10 w-10" 
                  style={{ color: "hsl(192 45% 55%)" }}
                />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">{t.brand.name}</h1>
                <p className="text-white/60 text-sm">{t.brand.tagline}</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="space-y-5"
          >
            {features.map((feature, index) => (
              <motion.div
                key={index}
                variants={fadeInUp}
                className="flex items-start gap-4 p-4 rounded-xl transition-colors"
                style={{ backgroundColor: "hsl(192 45% 42% / 0.08)" }}
              >
                <div 
                  className="p-2.5 rounded-lg shrink-0"
                  style={{ backgroundColor: "hsl(192 45% 42% / 0.2)" }}
                >
                  <feature.icon className="h-5 w-5" style={{ color: "hsl(192 45% 55%)" }} />
                </div>
                <div>
                  <h3 className="text-white font-medium mb-1">{feature.title}</h3>
                  <p className="text-white/50 text-sm">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          <motion.div 
            initial={prefersReducedMotion ? {} : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: prefersReducedMotion ? 0 : 0.4, duration: prefersReducedMotion ? 0 : 0.2 }}
            className="mt-12 pt-8 border-t border-white/10"
          >
            <p className="text-white/40 text-sm">
              {isRTL 
                ? "منصة موثوقة من قبل الشركات الرائدة في المنطقة"
                : "Trusted by leading enterprises in the region"
              }
            </p>
          </motion.div>
        </div>
      </div>

      <div 
        className="flex-1 flex flex-col"
        style={{ backgroundColor: "#0d1117" }}
      >
        <div className="flex justify-between items-center p-4">
          <Link href="/">
            <div className={`flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer ${isRTL ? "flex-row-reverse" : ""}`}>
              <ArrowIcon className="h-4 w-4" />
              <span>{t.auth.backToHome}</span>
            </div>
          </Link>
          <LanguageToggle />
        </div>

        <div className="flex-1 flex items-center justify-center p-4">
          <motion.div 
            initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: prefersReducedMotion ? 0 : 0.15 }}
            className="w-full max-w-md"
          >
            <div className="lg:hidden text-center mb-8">
              <div className="flex items-center justify-center gap-2 mb-2">
                <CircleDot className="h-8 w-8 text-primary" />
                <h1 className="text-3xl font-bold text-primary">{t.brand.name}</h1>
              </div>
              <p className="text-muted-foreground">{t.brand.tagline}</p>
            </div>

            <Card className="border-0 shadow-2xl" style={{ backgroundColor: "#161b22" }}>
              <CardContent className="pt-8 pb-8 px-8">
                <h2 className={`text-2xl font-bold text-foreground mb-2 ${isRTL ? "text-right" : "text-left"}`}>
                  {t.auth.welcomeBack}
                </h2>
                <p className={`text-muted-foreground text-sm mb-8 ${isRTL ? "text-right" : "text-left"}`}>
                  {t.auth.signInToContinue}
                </p>

                <form onSubmit={handleLogin} className="space-y-4">
                  {error && (
                    <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm text-center">
                      {error}
                    </div>
                  )}
                  
                  <div className="relative">
                    <Mail className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? "right-3" : "left-3"}`} />
                    <Input
                      type="email"
                      placeholder={t.auth.email}
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className={`h-12 bg-background border-border ${isRTL ? "pr-10 text-right" : "pl-10"}`}
                      style={{ backgroundColor: "#0d1117" }}
                      data-testid="input-email"
                      required
                    />
                  </div>

                  <div className="relative">
                    <Lock className={`absolute top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground ${isRTL ? "right-3" : "left-3"}`} />
                    <Input
                      type="password"
                      placeholder={t.auth.password}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={`h-12 bg-background border-border ${isRTL ? "pr-10 text-right" : "pl-10"}`}
                      style={{ backgroundColor: "#0d1117" }}
                      data-testid="input-password"
                      required
                    />
                  </div>

                  <Button
                    type="submit"
                    size="lg"
                    className="w-full h-12"
                    style={{ backgroundColor: "#238636", borderColor: "#238636" }}
                    disabled={isLoading}
                    data-testid="button-login"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span className="mr-2 ml-2">{t.auth.signingIn}</span>
                      </>
                    ) : (
                      t.auth.login
                    )}
                  </Button>

                  <Link href="/forgot-password">
                    <p className="text-center text-sm text-muted-foreground hover:text-foreground cursor-pointer">
                      {t.auth.forgotPassword}
                    </p>
                  </Link>

                  <div className="relative flex items-center justify-center my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-border"></div>
                    </div>
                    <span className="relative px-4 text-sm text-muted-foreground" style={{ backgroundColor: "#161b22" }}>
                      {t.auth.or}
                    </span>
                  </div>

                  <Button
                    type="button"
                    onClick={handleGoogleLogin}
                    variant="outline"
                    size="lg"
                    className="w-full h-12 gap-3"
                    disabled={isLoading}
                    data-testid="button-google-login"
                  >
                    <SiGoogle className="h-5 w-5" style={{ color: "#4285F4" }} />
                    <span>{t.auth.signInWithGoogle}</span>
                  </Button>

                  <p className="text-center text-xs text-muted-foreground">
                    {t.auth.googleWorkspaceOnly}
                  </p>

                  <div className="text-center pt-4">
                    <Link href="/register">
                      <p className="text-sm text-primary hover:underline cursor-pointer">
                        {t.auth.noAccount} {t.auth.createAccount}
                      </p>
                    </Link>
                  </div>
                </form>
              </CardContent>
            </Card>

            <p className="text-center text-xs text-muted-foreground mt-6">
              {t.auth.termsOfServiceLogin}
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
