import { Link } from "@tanstack/react-router"
import { ArrowRight } from "lucide-react"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Hero */}
      <main className="flex flex-1 flex-col items-center justify-center px-4">
        <Icons.logoBrand className="h-16 w-16" />

        <h1 className="mt-8 font-heading text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">Litestar Fullstack</h1>

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
  )
}
