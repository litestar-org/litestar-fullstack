import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { useAuthStore } from "@/lib/auth";

export const Route = createFileRoute("/_app")({
  component: AppLayout,
  beforeLoad: () => {
    const { isAuthenticated } = useAuthStore.getState();
    if (!isAuthenticated) {
      throw redirect({ to: '/login' });
    }
  },
});

function AppLayout() {
  return (
    <div className="container mx-auto py-8">
      <Outlet />
    </div>
  );
}
