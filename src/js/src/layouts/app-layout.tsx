// import { AppNav } from "@/components/app-nav"

import { AppSidebar } from "@/components/app-sidebar"
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { useAuthStore } from "@/lib/auth"
import { useTheme } from "@/lib/theme-context"
import { Outlet } from "@tanstack/react-router"
import { useEffect } from "react"
import { Toaster } from "sonner"

export function AppLayout() {
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const { theme } = useTheme()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <div className="flex min-h-screen flex-col">
      <Toaster richColors theme={theme} position="top-right" />
      {/* <AppNav /> */}
      <main className="flex flex-1">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
              <div className="flex items-center gap-2 px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <Breadcrumb>
                  <BreadcrumbList>
                    <BreadcrumbItem className="hidden md:block">
                      <BreadcrumbLink href="#">Building Your Application</BreadcrumbLink>
                    </BreadcrumbItem>
                    <BreadcrumbSeparator className="hidden md:block" />
                    <BreadcrumbItem>
                      <BreadcrumbPage>Data Fetching</BreadcrumbPage>
                    </BreadcrumbItem>
                  </BreadcrumbList>
                </Breadcrumb>
              </div>
            </header>
            <Outlet />
          </SidebarInset>
        </SidebarProvider>
      </main>
    </div>
  )
}
