import { Outlet } from "@tanstack/react-router";
import { Toaster } from "@/components/ui/toaster";

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
