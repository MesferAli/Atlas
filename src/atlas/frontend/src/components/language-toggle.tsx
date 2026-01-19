import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { Languages } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function LanguageToggle() {
  const { language, setLanguage } = useI18n();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" data-testid="button-language-toggle">
          <Languages className="h-5 w-5" />
          <span className="sr-only">Toggle language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem 
          onClick={() => setLanguage("ar")}
          className={language === "ar" ? "bg-accent" : ""}
          data-testid="menu-language-ar"
        >
          العربية
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setLanguage("en")}
          className={language === "en" ? "bg-accent" : ""}
          data-testid="menu-language-en"
        >
          English
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
