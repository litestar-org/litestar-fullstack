import { createFileRoute, redirect } from "@tanstack/react-router"
import { AppLayout } from "@/layouts/app-layout"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app")({
  component: AppLayout,
  beforeLoad: async () => {
    const { isAuthenticated, checkAuth } = useAuthStore.getState()

    // If not authenticated according to persisted state, redirect immediately
    if (!isAuthenticated) {
      throw redirect({ to: "/login" })
    }

    // Verify the session is still valid by checking with the server
    try {
      await checkAuth()
      // Re-check after verification - checkAuth updates the store if session is invalid
      const { isAuthenticated: stillAuthenticated } = useAuthStore.getState()
      if (!stillAuthenticated) {
        throw redirect({ to: "/login" })
      }
    } catch {
      // If checkAuth fails, clear state and redirect
      useAuthStore.setState({
        isAuthenticated: false,
        user: null,
        currentTeam: null,
      })
      throw redirect({ to: "/login" })
    }
  },
})
