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
    <div className="relative hidden h-full flex-col bg-brand-navy p-10 text-white lg:flex">
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
        ) : (
          <p className="text-lg font-medium leading-relaxed text-white/70">{description}</p>
        )}
      </div>
    </div>
  )
}
