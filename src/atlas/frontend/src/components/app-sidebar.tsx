import { Link, useLocation } from "wouter";
import {
  LayoutDashboard,
  Plug,
  GitBranch,
  Lightbulb,
  Shield,
  FileText,
  Sparkles,
  AlertTriangle,
  Settings,
  HelpCircle,
  CircleDot,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { useTranslations } from "@/lib/i18n";

export function AppSidebar() {
  const [location] = useLocation();
  const t = useTranslations();

  const isActive = (url: string) => {
    if (url === "/") return location === "/";
    return location.startsWith(url);
  };

  const mainNavItems = [
    { title: t.nav.dashboard, url: "/", icon: LayoutDashboard, testId: "nav-dashboard" },
    { title: t.nav.connectors, url: "/connectors", icon: Plug, testId: "nav-connectors" },
    { title: t.nav.mappings, url: "/mappings", icon: GitBranch, testId: "nav-mappings" },
  ];

  const aiNavItems = [
    { title: t.nav.recommendations, url: "/recommendations", icon: Lightbulb, badge: "3", testId: "nav-recommendations" },
    { title: t.nav.anomalies, url: "/anomalies", icon: AlertTriangle, badge: "1", testId: "nav-anomalies" },
  ];

  const governanceNavItems = [
    { title: t.nav.policies, url: "/policies", icon: Shield, testId: "nav-policies" },
    { title: t.nav.audit, url: "/audit", icon: FileText, testId: "nav-audit" },
  ];

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <Link href="/">
          <div className="flex items-center gap-3 cursor-pointer">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
              <CircleDot className="h-5 w-5 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-semibold tracking-tight">{t.brand.name}</span>
              <span className="text-xs text-muted-foreground">{t.brand.tagline}</span>
            </div>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{t.nav.platform}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavItems.map((item) => (
                <SidebarMenuItem key={item.testId}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item.url)}
                    data-testid={item.testId}
                  >
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel>{t.nav.intelligence}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {aiNavItems.map((item) => (
                <SidebarMenuItem key={item.testId}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item.url)}
                    data-testid={item.testId}
                  >
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                      {item.badge && (
                        <Badge variant="secondary" className="me-auto text-xs">
                          {item.badge}
                        </Badge>
                      )}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel>{t.nav.governance}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {governanceNavItems.map((item) => (
                <SidebarMenuItem key={item.testId}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item.url)}
                    data-testid={item.testId}
                  >
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild data-testid="nav-settings">
              <Link href="/settings">
                <Settings className="h-4 w-4" />
                <span>{t.nav.settings}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild data-testid="nav-help">
              <Link href="/help">
                <HelpCircle className="h-4 w-4" />
                <span>{t.nav.help}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
