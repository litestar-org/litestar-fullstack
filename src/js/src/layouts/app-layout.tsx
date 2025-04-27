import { Outlet } from "@tanstack/react-router";
import { Toaster } from "@/components/ui/toaster";
import { AppNav } from "@/components/app-nav";
import { TeamProvider } from "@/lib/team-context";

export function AppLayout() {
  return (
    <TeamProvider>
      <div className="min-h-screen bg-background">
        <AppNav />
        <main className="container mx-auto px-4 py-8">
          <Outlet />
        </main>
        <Toaster />
      </div>
    </TeamProvider>
  );
}
