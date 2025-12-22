import { AppSidebar } from "@/components/app-sidebar"
import { Separator } from "@/components/ui/separator"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { useAuthStore } from "@/lib/auth"
import { useTheme } from "@/lib/theme-context"
import { Outlet, useRouterState } from "@tanstack/react-router"
import { useEffect, useMemo } from "react"
import { Toaster } from "sonner"

export function AppLayout() {
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const currentTeam = useAuthStore((state) => state.currentTeam)
  const { theme } = useTheme()
  const pathname = useRouterState({ select: (state) => state.location.pathname })

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

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
    if (pathname === "/admin") {
      return { eyebrow: "Operations", title: "Admin" }
    }
    return { eyebrow: "Workspace", title: "Dashboard" }
  }, [currentTeam?.name, pathname])

  return (
    <div className="flex min-h-screen flex-col">
      <Toaster richColors theme={theme} position="top-right" />
      <main className="flex flex-1">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border/60 bg-background/80 backdrop-blur transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
              <div className="flex w-full items-center justify-between gap-4 px-4">
                <div className="flex items-center gap-2">
                  <SidebarTrigger className="-ml-1" />
                  <Separator orientation="vertical" className="mr-2 h-4" />
                  <div>
                    <p className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-muted-foreground">{header.eyebrow}</p>
                    <p className="font-['Space_Grotesk'] text-lg font-semibold text-foreground">{header.title}</p>
                  </div>
                </div>
                {currentTeam && (
                  <div className="hidden items-center gap-2 rounded-full border border-border/60 bg-card/80 px-3 py-1 text-xs font-medium text-muted-foreground md:flex">
                    Active team
                    <span className="text-foreground">{currentTeam.name}</span>
                  </div>
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
