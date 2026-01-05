import { Link, useRouterState } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

const navItems = [
  { label: "Dashboard", to: "/admin" },
  { label: "Users", to: "/admin/users" },
  { label: "Teams", to: "/admin/teams" },
  { label: "Audit log", to: "/admin/audit" },
] as const

export function AdminNav() {
  const pathname = useRouterState({ select: (state) => state.location.pathname })

  return (
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
  )
}
