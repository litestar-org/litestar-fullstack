import { AdminDashboard } from "@/components/admin/admin-dashboard"
import { useAuthStore } from "@/lib/auth"
import { createFileRoute } from "@tanstack/react-router"
import { useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/admin")({
  component: Admin,
})

function Admin() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  if (!user?.isSuperuser) {
    navigate({ to: "/home" as const })
    return null
  }

  return (
    <div className="container mx-auto space-y-6 py-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Administration</p>
          <h1 className="font-['Space_Grotesk'] text-3xl font-semibold">User management</h1>
          <p className="text-muted-foreground">Promote admins, audit access, and keep the directory tidy.</p>
        </div>
      </div>
      <AdminDashboard />
    </div>
  )
}

export default Admin
