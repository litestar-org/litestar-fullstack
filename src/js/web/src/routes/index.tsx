import { createFileRoute, redirect } from "@tanstack/react-router"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/")({
  component: IndexPage,
  beforeLoad: () => {
    const { isAuthenticated } = useAuthStore.getState()
    if (isAuthenticated) {
      throw redirect({ to: "/home" })
    }
    throw redirect({ to: "/landing" })
  },
})

function IndexPage() {
  return null
}
