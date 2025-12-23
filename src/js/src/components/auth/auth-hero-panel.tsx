import { Link } from "@tanstack/react-router"
import { Icons } from "@/components/icons"
import { RetroGrid } from "@/components/ui/retro-grid"

interface AuthHeroPanelProps {
  title?: string
  description?: string
  showTestimonial?: boolean
}

export function AuthHeroPanel({
  title = "Litestar Fullstack",
  description = "A modern, high-performance Python web framework with React, Vite, and shadcn/ui.",
  showTestimonial = true,
}: AuthHeroPanelProps) {
  return (
    <div className="relative hidden h-full flex-col bg-muted p-10 text-foreground lg:flex dark:border-r">
      <RetroGrid />
      <Link to="/" className="relative z-20">
        <div className="flex items-center font-medium text-lg">
          <Icons.logo className="mr-2 h-6 w-6" />
          {title}
        </div>
      </Link>

      <div className="relative z-20 mt-auto">
        {showTestimonial ? (
          <div className="space-y-4">
            <p className="text-lg font-medium leading-relaxed">{description}</p>
            <div className="flex items-center gap-4">
              <div className="flex -space-x-2">
                <div className="h-8 w-8 rounded-full bg-primary/20 ring-2 ring-background" />
                <div className="h-8 w-8 rounded-full bg-primary/30 ring-2 ring-background" />
                <div className="h-8 w-8 rounded-full bg-primary/40 ring-2 ring-background" />
              </div>
              <div className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Built with</span> Python, React, and modern tooling
              </div>
            </div>
          </div>
        ) : (
          <p className="text-lg font-medium leading-relaxed text-muted-foreground">{description}</p>
        )}
      </div>
    </div>
  )
}
