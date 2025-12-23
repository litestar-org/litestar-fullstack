import { Link } from "@tanstack/react-router"
import { motion, useScroll, useTransform } from "framer-motion"
import { ArrowRight, Clock, Code2, Lock, Rocket, Sparkles, Workflow } from "lucide-react"
import { useRef } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

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

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollY } = useScroll()
  const heroY = useTransform(scrollY, [0, 500], [0, 150])
  const heroOpacity = useTransform(scrollY, [0, 300], [1, 0])

  return (
    <div className="flex-1" ref={containerRef}>
      <div className="relative overflow-hidden">
        {/* Animated gradient orbs */}
        <div className="pointer-events-none absolute inset-0" aria-hidden>
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              x: [0, 50, 0],
              y: [0, 30, 0],
            }}
            transition={{ duration: 20, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            className="absolute -left-1/4 -top-1/4 h-150 w-150 rounded-full bg-primary/20 blur-3xl"
          />
          <motion.div
            animate={{
              scale: [1.2, 1, 1.2],
              x: [0, -30, 0],
              y: [0, 50, 0],
            }}
            transition={{ duration: 15, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
            className="absolute -right-1/4 top-1/3 h-125 w-125 rounded-full bg-accent/20 blur-3xl"
          />
        </div>

        <div className="container relative mx-auto flex min-h-[calc(100vh-2rem)] flex-col gap-16 px-4 py-12 md:py-16">
          {/* Hero with parallax */}
          <motion.div style={{ y: heroY, opacity: heroOpacity }} className="grid items-center gap-10 lg:grid-cols-[1.25fr_0.9fr] xl:grid-cols-[1.1fr_0.9fr]">
            <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-8 max-w-3xl">
              {/* Animated badge */}
              <motion.div variants={itemVariants}>
                <Badge className="bg-primary/10 text-primary border-primary/20 shadow-glow-sm">
                  <motion.span
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
                    className="mr-2 inline-block h-2 w-2 rounded-full bg-primary"
                  />
                  Litestar Fullstack Reference
                </Badge>
              </motion.div>

              <div className="space-y-4">
                <motion.h1 variants={itemVariants} className="font-['Space_Grotesk'] text-4xl font-semibold leading-tight text-foreground sm:text-5xl lg:text-6xl">
                  Build typed, blazing-fast apps with <span className="bg-linear-to-r from-primary via-primary to-accent bg-clip-text text-transparent">Litestar + Vite</span>
                </motion.h1>
                <motion.p variants={itemVariants} className="max-w-2xl text-lg text-muted-foreground">
                  A production-grade scaffold showcasing Litestar APIs, SAQ workers, JWT/OAuth security, and a polished React SPA with shadcn components.
                </motion.p>
              </div>

              <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
                <Button asChild size="lg" className="rounded-full px-7 shadow-glow-md hover:shadow-glow-lg transition-shadow duration-300">
                  <Link to="/signup">
                    Start with the template <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="rounded-full border-primary/40 px-6 text-primary hover:bg-primary/10">
                  <Link to="/login">Log in</Link>
                </Button>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock className="h-4 w-4 text-primary" />
                  <span className="text-sm">Deploy-ready in minutes</span>
                </div>
              </motion.div>

              <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
                {stats.map((stat, index) => (
                  <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 + index * 0.1 }}>
                    <Card hover className="border-none">
                      <CardContent className="p-4">
                        <div className="text-sm uppercase tracking-wide text-muted-foreground">{stat.label}</div>
                        <div className="font-semibold text-xl text-foreground">{stat.value}</div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="relative max-w-xl lg:max-w-lg xl:max-w-xl w-full mx-auto"
            >
              <div className="absolute inset-0 rounded-3xl bg-linear-to-br from-primary/20 via-primary/10 to-secondary/15 blur-2xl" aria-hidden />
              <Card className="relative border-primary/30 bg-card/80 shadow-2xl shadow-primary/20 backdrop-blur">
                <CardContent className="p-6">
                  <div className="mb-4 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                    <motion.div animate={{ rotate: [0, 360] }} transition={{ duration: 8, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}>
                      <Sparkles className="h-4 w-4 text-primary" />
                    </motion.div>
                    Live preview
                  </div>
                  <pre className="rounded-2xl bg-linear-to-br from-[#0f152a] via-[#0d1324] to-[#0b101f] p-4 md:p-5 text-xs sm:text-sm text-foreground overflow-x-auto">
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
            </motion.div>
          </motion.div>

          {/* Feature grid with staggered animations */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid gap-6 md:grid-cols-2 xl:grid-cols-4"
          >
            {featureCards.map((feature, index) => (
              <motion.div key={feature.title} variants={itemVariants} transition={{ delay: index * 0.1 }}>
                <Card hover glow className="h-full">
                  <CardContent className="space-y-3 p-5">
                    <motion.div
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      transition={{ type: "spring", stiffness: 400, damping: 17 }}
                      className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary"
                    >
                      <feature.icon className="h-5 w-5" />
                    </motion.div>
                    <h3 className="font-semibold text-lg">{feature.title}</h3>
                    <p className="text-muted-foreground text-sm leading-relaxed">{feature.copy}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>

          {/* CTA with scroll animation */}
          <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}>
            <Card className="border-none bg-linear-to-r from-primary/20 via-primary/15 to-accent/20 shadow-xl shadow-primary/20">
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
          </motion.div>

          {/* Footer */}
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="border-t border-border/60 pt-8 pb-4 text-sm text-muted-foreground">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.5 }} className="h-8 w-8 rounded-lg bg-primary/20" />
                <span className="font-semibold text-foreground">Litestar Fullstack</span>
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
            <div className="mt-3 text-xs text-muted-foreground">© {new Date().getFullYear()} Litestar. Crafted for fast, typed services.</div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
