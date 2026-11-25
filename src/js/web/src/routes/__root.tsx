import { createRootRoute, Outlet } from "@tanstack/react-router"
import { Toaster } from "sonner"
import { useTheme } from "@/lib/theme-context"

export const Route = createRootRoute({
  component: RootRoute,
})

function RootRoute() {
  const { theme } = useTheme()
  return (
    <>
      <Toaster richColors theme={theme} position="top-right" />
      <Outlet />
    </>
  )
}
