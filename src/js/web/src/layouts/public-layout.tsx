import { Outlet } from "@tanstack/react-router"
import { Moon, Sun } from "lucide-react"
import { Toaster } from "sonner"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/lib/theme-context"

export function PublicLayout() {
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="flex min-h-screen flex-col">
      <Toaster richColors theme={theme} position="top-right" />
      {/* Floating theme toggle for public pages */}
      <div className="fixed top-4 right-4 z-50">
        <Button
          variant="outline"
          size="icon"
          onClick={toggleTheme}
          className="size-9 rounded-full bg-background/80 backdrop-blur-sm border-border/50 shadow-lg"
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
        </Button>
      </div>
      <main className="flex flex-1">
        <Outlet />
      </main>
    </div>
  )
}
