import { useAuthStore } from "@/lib/auth";
import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/$")({
  component: NotFoundPage,
  beforeLoad: () => {
    const { isAuthenticated } = useAuthStore.getState();
    if (isAuthenticated) {
      throw redirect({ to: "/home" });
    }
    throw redirect({ to: "/landing" });
  },
});

function NotFoundPage() {
  return null;
}
