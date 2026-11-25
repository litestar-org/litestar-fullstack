import { createFileRoute, redirect } from "@tanstack/react-router"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app/admin")({
  beforeLoad: () => {
    if (!useAuthStore.getState().user?.isSuperuser) {
      throw redirect({ to: "/home" })
    }
  },
})
