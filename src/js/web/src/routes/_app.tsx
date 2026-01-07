import { createFileRoute, redirect } from "@tanstack/react-router"
import { AppLayout } from "@/layouts/app-layout"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app")({
  component: AppLayout,
  beforeLoad: async ({ location }) => {
    const { isAuthenticated, checkAuth } = useAuthStore.getState()

    // Build redirect search params preserving current URL
    // Note: location.search is an object in TanStack Router, use href for full path
    const redirectSearch = { redirect: location.href }

    // If not authenticated according to persisted state, redirect immediately
    if (!isAuthenticated) {
      throw redirect({ to: "/login", search: redirectSearch })
    }

    // Verify the session is still valid by checking with the server
    try {
      await checkAuth()
      // Re-check after verification - checkAuth updates the store if session is invalid
      const { isAuthenticated: stillAuthenticated } = useAuthStore.getState()
      if (!stillAuthenticated) {
        throw redirect({ to: "/login", search: redirectSearch })
      }
    } catch {
      // If checkAuth fails, clear state and redirect
      useAuthStore.setState({
        isAuthenticated: false,
        user: null,
        currentTeam: null,
      })
      throw redirect({ to: "/login", search: redirectSearch })
    }
  },
})
