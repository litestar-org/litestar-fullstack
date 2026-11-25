import { Link, useRouterState } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

const ADMIN_NAV_LINKS = [
  { label: "Dashboard", to: "/admin" },
  { label: "Users", to: "/admin/users" },
  { label: "Teams", to: "/admin/teams" },
  { label: "Queues", to: "/admin/queues" },
  { label: "Audit log", to: "/admin/audit" },
] as const

export function AdminNav() {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })

  return (
    <div className="flex flex-wrap gap-2">
      {ADMIN_NAV_LINKS.map((link) => {
        const isActive = pathname === link.to || (link.to !== "/admin" && pathname.startsWith(link.to))
        return (
          <Button key={link.to} asChild variant={isActive ? "default" : "outline"} size="sm">
            <Link to={link.to}>{link.label}</Link>
          </Button>
        )
      })}
    </div>
  )
}
