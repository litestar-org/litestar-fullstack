import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app/admin")({
  component: AdminLayout,
})

function AdminLayout() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  if (!user?.isSuperuser) {
    navigate({ to: "/home" as const })
    return null
  }

  // Just pass through to child routes - they handle their own layout
  return <Outlet />
}

export default AdminLayout
