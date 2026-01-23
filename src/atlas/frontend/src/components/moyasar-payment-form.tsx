import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { Shield, CreditCard, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useI18n } from "@/lib/i18n";
import { apiRequest } from "@/lib/queryClient";

interface MoyasarPaymentFormProps {
  planId: string;
  planName: string;
  amount: number;
  onSuccess: (paymentId: string) => void;
  onError: (error: string) => void;
  onCancel: () => void;
}

const cardFormSchema = z.object({
  name: z.string().min(2, "Cardholder name is required"),
  number: z.string()
    .min(13, "Card number must be at least 13 digits")
    .max(19, "Card number must be at most 19 digits")
    .regex(/^[\d\s]+$/, "Card number must contain only digits"),
  month: z.string()
    .min(1, "Expiry month is required")
    .max(2, "Invalid month")
    .regex(/^(0?[1-9]|1[0-2])$/, "Month must be 01-12"),
  year: z.string()
    .length(2, "Year must be 2 digits")
    .regex(/^\d{2}$/, "Year must be numeric"),
  cvc: z.string()
    .min(3, "CVC must be at least 3 digits")
    .max(4, "CVC must be at most 4 digits")
    .regex(/^\d+$/, "CVC must be numeric"),
});

type CardFormData = z.infer<typeof cardFormSchema>;

interface TokenizeRequest {
  publishable_api_key: string;
  name: string;
  number: string;
  month: string;
  year: string;
  cvc: string;
  callback_url?: string;
}

interface TokenizeResponse {
  id: string;
  status: string;
  message?: string;
  token?: string;
  type?: string;
}

interface PaymentInitiateRequest {
  planId: string;
  paymentMethod: "mada" | "creditcard";
  token: string;
}

interface PaymentInitiateResponse {
  success: boolean;
  paymentId?: string;
  status?: string;
  redirectUrl?: string;
  message?: string;
}

// Moyasar publishable key from environment (for tokenization only)
const MOYASAR_PUBLISHABLE_KEY = import.meta.env.VITE_MOYASAR_PUBLISHABLE_KEY || "";

function formatAmountArabic(amount: number): string {
  const arabicNumerals = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];
  const formatted = amount.toFixed(2);
  return formatted.replace(/\d/g, (digit) => arabicNumerals[parseInt(digit, 10)]);
}

export function MoyasarPaymentForm({
  planId,
  planName,
  amount,
  onSuccess,
  onError,
  onCancel,
}: MoyasarPaymentFormProps) {
  const { t, isRTL, language } = useI18n();
  const [paymentMethod, setPaymentMethod] = useState<"mada" | "creditcard">("mada");

  const paymentTranslations = {
    ar: {
      title: "الدفع الآمن",
      description: "أدخل بيانات بطاقتك لإتمام الدفع",
      amount: "المبلغ",
      currency: "ر.س",
      mada: "مدى",
      creditcard: "فيزا / ماستركارد",
      cardholderName: "اسم حامل البطاقة",
      cardNumber: "رقم البطاقة",
      expiryMonth: "شهر الانتهاء",
      expiryYear: "سنة الانتهاء",
      cvc: "رمز الأمان",
      pay: "ادفع الآن",
      cancel: "إلغاء",
      processing: "جاري المعالجة...",
      securePayment: "دفع آمن ومشفر",
      poweredBy: "مدعوم من Moyasar",
      cardholderPlaceholder: "الاسم كما يظهر على البطاقة",
      cardNumberPlaceholder: "0000 0000 0000 0000",
      monthPlaceholder: "شهر",
      yearPlaceholder: "سنة",
      cvcPlaceholder: "CVV",
      subscribeTo: "الاشتراك في",
    },
    en: {
      title: "Secure Payment",
      description: "Enter your card details to complete payment",
      amount: "Amount",
      currency: "SAR",
      mada: "Mada",
      creditcard: "Visa / Mastercard",
      cardholderName: "Cardholder Name",
      cardNumber: "Card Number",
      expiryMonth: "Expiry Month",
      expiryYear: "Expiry Year",
      cvc: "Security Code",
      pay: "Pay Now",
      cancel: "Cancel",
      processing: "Processing...",
      securePayment: "Secure & Encrypted Payment",
      poweredBy: "Powered by Moyasar",
      cardholderPlaceholder: "Name as it appears on card",
      cardNumberPlaceholder: "0000 0000 0000 0000",
      monthPlaceholder: "MM",
      yearPlaceholder: "YY",
      cvcPlaceholder: "CVV",
      subscribeTo: "Subscribe to",
    },
  };

  const pt = paymentTranslations[language] || paymentTranslations.ar;

  const form = useForm<CardFormData>({
    resolver: zodResolver(cardFormSchema),
    defaultValues: {
      name: "",
      number: "",
      month: "",
      year: "",
      cvc: "",
    },
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const [processingError, setProcessingError] = useState<string | null>(null);

  const initiatePaymentMutation = useMutation({
    mutationFn: async (data: PaymentInitiateRequest): Promise<PaymentInitiateResponse> => {
      const response = await apiRequest("POST", "/api/payments/initiate", data);
      return response.json();
    },
    onSuccess: (response) => {
      setIsProcessing(false);
      if (response.redirectUrl) {
        // 3D Secure redirect
        window.location.href = response.redirectUrl;
      } else if (response.status === "paid" && response.paymentId) {
        onSuccess(response.paymentId);
      } else if (response.status === "pending_3ds" && response.redirectUrl) {
        window.location.href = response.redirectUrl;
      } else {
        onError(response.message || "Payment failed");
      }
    },
    onError: (error: Error) => {
      setIsProcessing(false);
      onError(error.message || "Payment failed");
    },
  });

  const tokenizeCard = async (cardData: CardFormData): Promise<string> => {
    const cleanedNumber = cardData.number.replace(/\s/g, "");
    
    // SECURITY: Publishable key is required for PCI-compliant tokenization
    // Card data must NEVER be sent to our backend - always tokenize with Moyasar
    if (!MOYASAR_PUBLISHABLE_KEY) {
      throw new Error("Payment system not configured. Please contact support.");
    }

    // Tokenize directly with Moyasar from browser (PCI-compliant)
    const tokenizeData: TokenizeRequest = {
      publishable_api_key: MOYASAR_PUBLISHABLE_KEY,
      name: cardData.name,
      number: cleanedNumber,
      month: cardData.month.padStart(2, "0"),
      year: cardData.year,
      cvc: cardData.cvc,
    };

    const response = await fetch("https://api.moyasar.com/v1/tokens", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tokenizeData),
    });

    const result: TokenizeResponse = await response.json();

    if (!response.ok || !result.id) {
      throw new Error(result.message || "Failed to tokenize card");
    }

    return result.id;
  };

  const onSubmit = async (data: CardFormData) => {
    setIsProcessing(true);
    setProcessingError(null);

    try {
      // Step 1: Tokenize card data directly with Moyasar (PCI-compliant)
      const token = await tokenizeCard(data);

      // Step 2: Send only the token to our backend (no card data)
      initiatePaymentMutation.mutate({
        planId,
        paymentMethod,
        token,
      });
    } catch (error) {
      setIsProcessing(false);
      const message = error instanceof Error ? error.message : "Payment processing failed";
      setProcessingError(message);
      onError(message);
    }
  };

  const displayAmount = isRTL 
    ? `${formatAmountArabic(amount)} ${pt.currency}`
    : `${pt.currency} ${amount.toFixed(2)}`;

  const CardFormFields = () => (
    <div className="space-y-4">
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{pt.cardholderName}</FormLabel>
            <FormControl>
              <Input
                {...field}
                data-testid="input-card-name"
                placeholder={pt.cardholderPlaceholder}
                dir={isRTL ? "rtl" : "ltr"}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="number"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{pt.cardNumber}</FormLabel>
            <FormControl>
              <Input
                {...field}
                data-testid="input-card-number"
                placeholder={pt.cardNumberPlaceholder}
                dir="ltr"
                maxLength={19}
                onChange={(e) => {
                  const value = e.target.value.replace(/\s/g, "").replace(/(\d{4})/g, "$1 ").trim();
                  field.onChange(value);
                }}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="grid grid-cols-3 gap-4">
        <FormField
          control={form.control}
          name="month"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{pt.expiryMonth}</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  data-testid="input-card-expiry-month"
                  placeholder={pt.monthPlaceholder}
                  dir="ltr"
                  maxLength={2}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="year"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{pt.expiryYear}</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  data-testid="input-card-expiry-year"
                  placeholder={pt.yearPlaceholder}
                  dir="ltr"
                  maxLength={2}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="cvc"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{pt.cvc}</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  data-testid="input-card-cvc"
                  placeholder={pt.cvcPlaceholder}
                  dir="ltr"
                  maxLength={4}
                  type="password"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </div>
  );

  return (
    <Card className="w-full max-w-md mx-auto" data-testid="form-moyasar-payment">
      <CardHeader className="text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Shield className="h-5 w-5 text-primary" />
          <span className="text-sm text-muted-foreground">{pt.securePayment}</span>
        </div>
        <CardTitle>{pt.title}</CardTitle>
        <CardDescription>
          {pt.subscribeTo} {planName}
        </CardDescription>
        <div className="mt-4 p-4 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground">{pt.amount}</p>
          <p className="text-3xl font-bold text-primary">{displayAmount}</p>
        </div>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Tabs
              defaultValue="mada"
              onValueChange={(value) => setPaymentMethod(value as "mada" | "creditcard")}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="mada" data-testid="tab-mada">
                  <CreditCard className="h-4 w-4 me-2" />
                  {pt.mada}
                </TabsTrigger>
                <TabsTrigger value="creditcard" data-testid="tab-creditcard">
                  <CreditCard className="h-4 w-4 me-2" />
                  {pt.creditcard}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="mada" className="mt-4">
                <CardFormFields />
              </TabsContent>

              <TabsContent value="creditcard" className="mt-4">
                <CardFormFields />
              </TabsContent>
            </Tabs>

            <div className="flex flex-col gap-3 pt-4">
              <Button
                type="submit"
                className="w-full"
                disabled={initiatePaymentMutation.isPending}
                data-testid="button-submit-payment"
              >
                {initiatePaymentMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin me-2" />
                    {pt.processing}
                  </>
                ) : (
                  <>
                    {pt.pay} - {displayAmount}
                  </>
                )}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={initiatePaymentMutation.isPending}
                data-testid="button-cancel-payment"
              >
                {pt.cancel}
              </Button>
            </div>

            <p className="text-xs text-center text-muted-foreground">
              {pt.poweredBy}
            </p>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
