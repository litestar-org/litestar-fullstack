import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Link } from "@tanstack/react-router"
import { motion } from "framer-motion"
import { ArrowRight, Clock, Code2, Lock, Rocket, Sparkles, Workflow } from "lucide-react"

const featureCards = [
  {
    icon: Rocket,
    title: "Performant by default",
    copy: "Async-first, uvicorn/granian ready. Ship APIs that stay fast under load.",
  },
  {
    icon: Code2,
    title: "Typed end-to-end",
    copy: "OpenAPI + SDK generation keep your React routes and Python services in lockstep.",
  },
  {
    icon: Workflow,
    title: "Fullstack workflow",
    copy: "Vite-powered SPA, background jobs via SAQ, structured logging baked in.",
  },
  {
    icon: Lock,
    title: "Production-grade security",
    copy: "JWT auth, OAuth, CSRF protection, and sane defaults ready out of the box.",
  },
]

const stats = [
  { label: "Cold start", value: "<90ms" },
  { label: "Type coverage", value: "100%" },
  { label: "SDK updates", value: "On build" },
]

export function LandingPage() {
  return (
    <div className="flex-1">
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 opacity-70 blur-3xl" aria-hidden>
          <div className="bg-[radial-gradient(circle_at_20%_20%,rgba(18,100,159,0.25),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(227,198,122,0.18),transparent_30%),radial-gradient(circle_at_50%_90%,rgba(109,119,123,0.22),transparent_35%)] h-full w-full" />
        </div>

        <div className="container relative mx-auto flex min-h-[calc(100vh-2rem)] flex-col gap-16 px-4 py-12 md:py-16">
          {/* Hero */}
          <div className="grid items-center gap-10 lg:grid-cols-[1.25fr_0.9fr] xl:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-8 max-w-3xl">
              <Badge className="bg-secondary text-secondary-foreground shadow-md shadow-secondary/30">
                Litestar Fullstack Reference
              </Badge>
              <div className="space-y-4">
                <motion.h1
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.45 }}
                  className="font-['Space_Grotesk'] text-4xl font-semibold leading-tight text-foreground sm:text-5xl lg:text-6xl"
                >
                  Build typed, blazing-fast apps with Litestar + Vite.
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.05 }}
                  className="max-w-2xl text-lg text-muted-foreground"
                >
                  A production-grade scaffold showcasing Litestar APIs, SAQ workers, JWT/OAuth security, and a polished React SPA with shadcn components.
                </motion.p>
              </div>

              <div className="flex flex-wrap gap-4">
                <Button asChild size="lg" className="rounded-full px-7 shadow-lg shadow-primary/25">
                  <Link to="/signup">
                    Start with the template <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="rounded-full border-primary/40 px-6 text-primary hover:bg-primary/10">
                  <Link to="/login">Log in</Link>
                </Button>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock className="h-4 w-4 text-secondary" />
                  <span className="text-sm">Deploy-ready in minutes</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-4">
                {stats.map((stat) => (
                  <Card key={stat.label} className="border-none bg-card/70 shadow-lg shadow-primary/10 backdrop-blur">
                    <CardContent className="p-4">
                      <div className="text-sm uppercase tracking-wide text-muted-foreground">{stat.label}</div>
                      <div className="font-semibold text-xl text-foreground">{stat.value}</div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div className="relative max-w-xl lg:max-w-lg xl:max-w-xl w-full mx-auto">
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-primary/20 via-primary/10 to-secondary/15 blur-2xl" aria-hidden />
              <Card className="relative border-primary/30 bg-card/80 shadow-2xl shadow-primary/20 backdrop-blur">
                <CardContent className="p-6">
                  <div className="mb-4 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">
                    <Sparkles className="h-4 w-4 text-secondary" /> Live preview
                  </div>
                  <pre className="rounded-2xl bg-gradient-to-br from-[#0f152a] via-[#0d1324] to-[#0b101f] p-4 md:p-5 text-xs sm:text-sm text-foreground overflow-x-auto">
{`from litestar import Litestar, get
from litestar.middleware.session import SessionMiddlewareConfig
from litestar_vite import VitePlugin, ViteConfig, PathConfig

@get("/health")
def ready() -> dict[str, str]:
    return {"status": "ok"}

app = Litestar(
    route_handlers=[ready],
    plugins=[
        VitePlugin(config=ViteConfig(paths=PathConfig(root="src/js"))),
    ],
    middleware=[SessionMiddlewareConfig(secret="change-me").middleware],
)`}
                  </pre>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Feature grid */}
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {featureCards.map((feature) => (
              <Card key={feature.title} className="border-border/60 bg-card/70 shadow-lg shadow-primary/10 backdrop-blur">
                <CardContent className="space-y-3 p-5">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary">
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-lg">{feature.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">{feature.copy}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* CTA */}
          <Card className="border-none bg-gradient-to-r from-primary/20 via-primary/15 to-secondary/20 shadow-xl shadow-primary/20">
            <CardContent className="flex flex-col items-start gap-6 px-6 py-10 md:flex-row md:items-center md:justify-between md:px-10">
              <div className="space-y-3">
                <h2 className="font-['Space_Grotesk'] text-3xl font-semibold text-foreground">Ship your next service with confidence.</h2>
                <p className="max-w-xl text-muted-foreground">
                  Explore the reference routes, queues, auth flows, and frontend patterns to accelerate your own Litestar deployments.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button asChild size="lg" className="rounded-full px-7">
                  <Link to="/signup">Create an account</Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="rounded-full border-foreground/20 px-6">
                  <Link to="/login">View dashboard</Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="border-t border-border/60 pt-8 pb-4 text-sm text-muted-foreground">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-primary/20" />
                <span className="font-semibold text-foreground">Litestar Fullstack</span>
              </div>
              <div className="flex gap-6">
                <Link to="/privacy" className="transition-colors hover:text-foreground">
                  Privacy
                </Link>
                <Link to="/terms" className="transition-colors hover:text-foreground">
                  Terms
                </Link>
              </div>
            </div>
            <div className="mt-3 text-xs text-muted-foreground">© {new Date().getFullYear()} Litestar. Crafted for fast, typed services.</div>
          </div>
        </div>
      </div>
    </div>
  )
}
