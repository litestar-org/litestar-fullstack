import { createFileRoute, redirect } from "@tanstack/react-router"
import { AppLayout } from "@/layouts/app-layout"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app")({
  component: AppLayout,
  beforeLoad: async ({ location }) => {
    const authenticated = await useAuthStore.getState().checkAuth()
    if (!authenticated) {
      throw redirect({ to: "/login", search: { redirect: location.href } })
    }
  },
})
