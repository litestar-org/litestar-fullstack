import { Link, Outlet, useRouterState } from "@tanstack/react-router"
import { useMemo } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { Separator } from "@/components/ui/separator"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { useAuthStore } from "@/lib/auth"

export function AppLayout() {
  const currentTeam = useAuthStore((state) => state.currentTeam)
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })

  const header = useMemo(() => {
    if (pathname === "/home") {
      return { eyebrow: "Overview", title: "Home" }
    }
    if (pathname === "/teams") {
      return { eyebrow: "Workspace", title: "Teams" }
    }
    if (pathname === "/teams/new") {
      return { eyebrow: "Workspace", title: "Create team" }
    }
    if (pathname.startsWith("/teams/")) {
      return { eyebrow: "Workspace", title: currentTeam?.name ?? "Team" }
    }
    if (pathname.startsWith("/admin")) {
      return { eyebrow: "Operations", title: "Admin" }
    }
    if (pathname.startsWith("/profile")) {
      return { eyebrow: "Account", title: "Profile" }
    }
    return { eyebrow: "Workspace", title: "Dashboard" }
  }, [currentTeam?.name, pathname])

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex flex-1">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border/60 bg-background/80 backdrop-blur">
              <div className="flex w-full items-center justify-between gap-4 px-4">
                <div className="flex items-center gap-2">
                  <SidebarTrigger className="-ml-1" />
                  <Separator orientation="vertical" className="mr-2 h-4" />
                  <div>
                    <p className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-muted-foreground">{header.eyebrow}</p>
                    <p className="font-heading text-lg font-semibold text-foreground">{header.title}</p>
                  </div>
                </div>
                {currentTeam && pathname !== "/teams/new" && !pathname.startsWith(`/teams/${currentTeam.id}`) && (
                  <Link
                    to="/teams/$teamId"
                    params={{ teamId: currentTeam.id }}
                    className="hidden items-center gap-2 rounded-full border border-border/60 bg-card/80 px-3 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground md:flex"
                  >
                    Active team
                    <span className="text-foreground">{currentTeam.name}</span>
                  </Link>
                )}
              </div>
            </header>
            <Outlet />
          </SidebarInset>
        </SidebarProvider>
      </main>
    </div>
  )
}
