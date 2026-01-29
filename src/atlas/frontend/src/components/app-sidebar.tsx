import { Link, useLocation } from "wouter";
import {
  LayoutDashboard,
  Database,
  FileText,
  Settings,
  HelpCircle,
  Shield,
  LogOut,
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
import { useAuth } from "@/hooks/use-auth";

export function AppSidebar() {
  const [location] = useLocation();
  const { user, logout } = useAuth();

  const isActive = (url: string) => {
    if (url === "/") return location === "/" || location === "/dashboard";
    return location.startsWith(url);
  };

  const mainNavItems = [
    {
      title: "Dashboard",
      url: "/",
      icon: LayoutDashboard,
      testId: "nav-dashboard",
    },
    {
      title: "Oracle Chat",
      url: "/dashboard",
      icon: Database,
      testId: "nav-oracle",
      badge: "AI",
    },
  ];

  const governanceNavItems = [
    {
      title: "Audit Log",
      url: "/audit",
      icon: FileText,
      testId: "nav-audit",
    },
    {
      title: "PDPL Compliance",
      url: "/settings",
      icon: Shield,
      testId: "nav-pdpl",
    },
  ];

  return (
    <Sidebar>
      {/* Brand Header */}
      <SidebarHeader className="px-4 py-5">
        <Link href="/">
          <div className="flex items-center gap-3 cursor-pointer group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 shadow-md group-hover:shadow-lg transition-shadow">
              <span className="text-sm font-bold text-primary-foreground">A</span>
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight">Atlas</span>
              <span className="text-[10px] text-muted-foreground tracking-wide uppercase">
                Oracle Connector Lite
              </span>
            </div>
          </div>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {/* Platform */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest text-muted-foreground/60 font-semibold px-3">
            Platform
          </SidebarGroupLabel>
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
                      <span className="flex-1">{item.title}</span>
                      {item.badge && (
                        <Badge className="h-4 px-1.5 text-[9px] font-semibold bg-primary/10 text-primary border-0">
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

        {/* Governance */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest text-muted-foreground/60 font-semibold px-3">
            Governance
          </SidebarGroupLabel>
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

      {/* Footer */}
      <SidebarFooter className="px-3 pb-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild data-testid="nav-settings">
              <Link href="/settings">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild data-testid="nav-help">
              <Link href="/help">
                <HelpCircle className="h-4 w-4" />
                <span>Help</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {/* User Card */}
        {user && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center gap-3 px-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5 text-xs font-semibold text-primary shrink-0">
                {(user.firstName?.[0] || user.email?.[0] || "U").toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">
                  {user.firstName
                    ? `${user.firstName} ${user.lastName || ""}`
                    : user.email}
                </p>
                <p className="text-[10px] text-muted-foreground capitalize">
                  {user.role || "viewer"}
                </p>
              </div>
              <button
                onClick={logout}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Sign out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
