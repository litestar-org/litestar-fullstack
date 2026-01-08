import { Link } from "@tanstack/react-router"
import { ArrowRight, Moon, Sun } from "lucide-react"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { RetroGrid } from "@/components/ui/retro-grid"
import { useTheme } from "@/lib/theme-context"

export function LandingPage() {
  const { toggleTheme, theme } = useTheme()

  return (
    <div className="relative flex min-h-screen w-full">
      {/* Left panel with RetroGrid - hidden on mobile */}
      <div className="relative hidden min-h-screen w-1/2 max-w-2xl flex-col bg-brand-navy p-10 text-white lg:flex">
        <RetroGrid />
        <Link to="/" className="relative z-20">
          <div className="flex items-center font-medium text-lg">
            <Icons.logo className="mr-2 h-6 w-6" />
            Litestar Fullstack
          </div>
        </Link>
        <div className="relative z-20 mt-auto">
          <p className="text-lg font-medium leading-relaxed">Build high-performance web applications with Python and React. Seamless SPA experience powered by Vite.</p>
          <div className="mt-4 flex items-center gap-4">
            <div className="flex -space-x-1">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 ring-2 ring-brand-navy backdrop-blur-sm">
                <Icons.python className="h-5 w-5" />
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 ring-2 ring-brand-navy backdrop-blur-sm">
                <Icons.react className="h-5 w-5 text-[#61DAFB]" />
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 ring-2 ring-brand-navy backdrop-blur-sm">
                <Icons.vite className="h-5 w-5" />
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 ring-2 ring-brand-navy backdrop-blur-sm">
                <Icons.typescript className="h-5 w-5" />
              </div>
            </div>
            <div className="text-sm text-white/70">
              <span className="font-medium text-white">Built with</span> Python, React & modern tooling
            </div>
          </div>
        </div>
      </div>

      {/* Right panel with content */}
      <div className="flex flex-1 flex-col bg-brand-gray-light dark:bg-background">
        {/* Header with theme toggle and sign in */}
        <div className="flex items-center justify-end gap-2 p-4 md:p-8">
          <Button variant="ghost" size="icon" onClick={toggleTheme} className="size-9 rounded-full" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
            {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
          </Button>
          <Button asChild variant="ghost">
            <Link to="/login">Sign in</Link>
          </Button>
        </div>

        {/* Main content - centered */}
        <main className="flex flex-1 flex-col items-center justify-center px-4 pb-16">
          <Icons.logoBrand className="h-16 w-16" />

          <h1 className="mt-8 font-heading text-4xl font-bold tracking-tight text-foreground sm:text-5xl">Litestar Fullstack</h1>

          <p className="mt-4 max-w-md text-center text-lg text-muted-foreground">A production-ready Python + React reference application</p>

          <div className="mt-10 flex gap-4">
            <Button asChild size="lg">
              <Link to="/signup">Try the demo</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <a href="https://github.com/litestar-org/litestar-fullstack" target="_blank" rel="noopener noreferrer">
                View source
                <ArrowRight className="ml-2 h-4 w-4" />
              </a>
            </Button>
          </div>
        </main>

        {/* Footer */}
        <footer className="py-6 text-center text-sm text-muted-foreground">© {new Date().getFullYear()} Litestar Organization · MIT License</footer>
      </div>
    </div>
  )
}
