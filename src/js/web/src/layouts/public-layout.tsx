import { Link, Outlet, useRouterState } from "@tanstack/react-router"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/lib/theme-context"

export function PublicLayout() {
  const { toggleTheme, theme } = useTheme()
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })

  const isLandingPage = pathname === "/" || pathname === "/landing"
  const isAuthPage =
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/forgot-password" ||
    pathname === "/reset-password" ||
    pathname === "/mfa-challenge" ||
    pathname === "/verify-email" ||
    pathname.startsWith("/auth/")

  // Landing and auth pages bring their own navigation; only content pages (terms, privacy, about) get the site header and footer.
  const isContentPage = !isLandingPage && !isAuthPage

  return (
    <div className="flex min-h-screen flex-col">
      {isContentPage && (
        <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur">
          <div className="container mx-auto flex h-14 items-center justify-between px-4">
            <Link to="/" className="flex items-center gap-2 text-foreground hover:opacity-80 transition-opacity">
              <div className="h-7 w-7 rounded-lg bg-primary/20" />
              <span className="font-semibold">Litestar Fullstack</span>
            </Link>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="icon" onClick={toggleTheme} className="size-9 rounded-full" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
                {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
              </Button>
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">Log in</Link>
              </Button>
              <Button asChild size="sm">
                <Link to="/signup">Sign up</Link>
              </Button>
            </div>
          </div>
        </header>
      )}

      <main className="flex flex-1">
        <Outlet />
      </main>

      {isContentPage && (
        <footer className="border-t border-border/60 bg-background/80">
          <div className="container mx-auto px-4 py-6">
            <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-md bg-primary/20" />
                <span className="font-medium text-foreground">Litestar Fullstack</span>
              </div>
              <div className="flex gap-6">
                <Link to="/privacy" className="transition-colors hover:text-foreground">
                  Privacy
                </Link>
                <Link to="/terms" className="transition-colors hover:text-foreground">
                  Terms
                </Link>
                <Link to="/about" className="transition-colors hover:text-foreground">
                  About
                </Link>
              </div>
            </div>
          </div>
        </footer>
      )}
    </div>
  )
}
