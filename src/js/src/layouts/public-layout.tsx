import { useTheme } from "@/lib/theme-context"
import { Outlet } from "@tanstack/react-router"
import { Toaster } from "sonner"

export function PublicLayout() {
  const { theme } = useTheme()

  return (
    <div className="flex min-h-screen flex-col">
      <Toaster richColors theme={theme} position="top-right" />
      <main className="flex flex-1">
        <Outlet />
      </main>
    </div>
  )
}
