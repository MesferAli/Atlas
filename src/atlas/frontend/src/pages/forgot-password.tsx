import { useState } from "react";
import { Mail, ArrowLeft, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/lib/i18n";
import { LanguageToggle } from "@/components/language-toggle";
import { Link } from "wouter";

export default function ForgotPasswordPage() {
  const { t, language } = useI18n();
  const isRTL = language === "ar";
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!email) return;
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsLoading(false);
    setIsSubmitted(true);
  };

  const ArrowIcon = isRTL ? ArrowRight : ArrowLeft;

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4"
      dir={isRTL ? "rtl" : "ltr"}
      style={{ backgroundColor: "#0d1117" }}
    >
      <div className="absolute top-4 left-4 right-4 flex justify-end">
        <LanguageToggle />
      </div>

      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-primary">{t.brand.name}</h1>
          <p className="text-muted-foreground">{t.brand.tagline}</p>
        </div>

        <Card className="border-0" style={{ backgroundColor: "#161b22" }}>
          <CardContent className="pt-6 pb-6 px-6">
            <Link href="/login">
              <div className={`flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer mb-6 ${isRTL ? "flex-row-reverse justify-end" : ""}`}>
                <ArrowIcon className="h-4 w-4" />
                <span>{t.auth.backToLogin}</span>
              </div>
            </Link>

            {isSubmitted ? (
              <div className="text-center space-y-4 py-8">
                <div className="flex justify-center">
                  <div className="p-4 rounded-full bg-primary/10">
                    <CheckCircle2 className="h-12 w-12 text-primary" />
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-foreground">
                  {t.auth.resetLinkSent}
                </h2>
                <p className="text-muted-foreground">
                  {t.auth.resetLinkSentDesc}
                </p>
                <Link href="/login">
                  <Button variant="outline" size="lg" className="mt-4">
                    {t.auth.backToLogin}
                  </Button>
                </Link>
              </div>
            ) : (
              <>
                <h2 className={`text-2xl font-bold text-foreground mb-2 ${isRTL ? "text-right" : "text-left"}`}>
                  {t.auth.forgotPasswordTitle}
                </h2>
                <p className={`text-muted-foreground mb-6 ${isRTL ? "text-right" : "text-left"}`}>
                  {t.auth.forgotPasswordSubtitle}
                </p>

                <div className="space-y-4">
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
                    />
                  </div>

                  <Button
                    onClick={handleSubmit}
                    size="lg"
                    className="w-full h-12"
                    disabled={isLoading || !email}
                    data-testid="button-send-reset"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span className="mr-2 ml-2">{t.common.loading}</span>
                      </>
                    ) : (
                      t.auth.sendResetLink
                    )}
                  </Button>

                  <div className="text-center pt-4">
                    <Link href="/login">
                      <p className="text-sm text-muted-foreground hover:text-foreground cursor-pointer">
                        {t.auth.backToLogin}
                      </p>
                    </Link>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
