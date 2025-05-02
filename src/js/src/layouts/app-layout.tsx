import { AppNav } from "@/components/app-nav";
import { useAuthStore } from "@/lib/auth";
import { TeamProvider } from "@/lib/team-context";
import { ThemeProvider } from "@/lib/theme-context";
import { Outlet } from "@tanstack/react-router";
import { useEffect } from "react";
import { Toaster } from "sonner";
import { Sidebar } from "../components/sidebar";

export function AppLayout() {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <ThemeProvider>
      <TeamProvider>
        <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
          <AppNav />
          <div className="flex h-[calc(100vh-4rem)]">
            <Sidebar />
            <main className="flex-1 overflow-auto p-8">
              <Outlet />
            </main>
          </div>
          <Toaster richColors position="top-right" />
        </div>
      </TeamProvider>
    </ThemeProvider>
  );
}
