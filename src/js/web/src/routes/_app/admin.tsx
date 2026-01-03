import { Link, Outlet, createFileRoute, useNavigate, useRouterState } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_app/admin")({
  component: AdminLayout,
})

function AdminLayout() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const pathname = useRouterState({ select: (state) => state.location.pathname })

  if (!user?.isSuperuser) {
    navigate({ to: "/home" as const })
    return null
  }

  const navItems = [
    { label: "Dashboard", to: "/admin" },
    { label: "Users", to: "/admin/users" },
    { label: "Teams", to: "/admin/teams" },
    { label: "Audit log", to: "/admin/audit" },
  ]

  return (
    <div className="container mx-auto space-y-6 py-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Administration</p>
          <h1 className="font-['Space_Grotesk'] text-3xl font-semibold">Admin console</h1>
          <p className="text-muted-foreground">Review activity, manage users, and oversee teams.</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {navItems.map((item) => {
          const isActive = pathname === item.to || (item.to !== "/admin" && pathname.startsWith(item.to))
          return (
            <Button key={item.to} asChild variant={isActive ? "default" : "outline"} size="sm">
              <Link to={item.to}>{item.label}</Link>
            </Button>
          )
        })}
      </div>
      <Outlet />
    </div>
  )
}

export default AdminLayout
