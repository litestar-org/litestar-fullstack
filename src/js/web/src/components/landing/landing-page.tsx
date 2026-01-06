import { Link } from "@tanstack/react-router"
import { motion } from "framer-motion"
import { ArrowRight, Check, Database, Key, Mail, Server, Users, Zap } from "lucide-react"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

const techStack = [
  { name: "Litestar", icon: Icons.logoBrand, description: "Python API framework" },
  { name: "React 19", icon: Icons.react, description: "Frontend library" },
  { name: "Vite", icon: Icons.vite, description: "Build tooling" },
  { name: "TypeScript", icon: Icons.typescript, description: "Type safety" },
  { name: "PostgreSQL", icon: Icons.postgresql, description: "Database" },
  { name: "Redis", icon: Icons.redis, description: "Cache & queues" },
]

const features = [
  {
    icon: Key,
    title: "Authentication",
    items: ["JWT tokens", "OAuth2 (Google/GitHub)", "Email verification", "Password reset", "TOTP 2FA"],
  },
  {
    icon: Users,
    title: "Teams & Roles",
    items: ["Team workspaces", "Member invitations", "Role-based access", "Admin dashboard"],
  },
  {
    icon: Server,
    title: "Backend",
    items: ["Async Python API", "OpenAPI generation", "Type-safe schemas", "SQLAlchemy ORM"],
  },
  {
    icon: Zap,
    title: "Background Jobs",
    items: ["SAQ worker queue", "Redis-backed tasks", "Email delivery", "Job monitoring"],
  },
  {
    icon: Database,
    title: "Database",
    items: ["PostgreSQL", "Alembic migrations", "Advanced Alchemy", "Audit logging"],
  },
  {
    icon: Mail,
    title: "Email",
    items: ["React Email templates", "MJML support", "MailHog dev server", "Async delivery"],
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

export function LandingPage() {
  return (
    <div className="flex-1 bg-background">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border/40">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-linear-to-br from-primary/5 via-transparent to-accent/5" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(var(--primary-rgb),0.1),transparent_50%)]" />

        <div className="container relative mx-auto px-4 py-16 md:py-24 lg:py-32">
          <motion.div initial="hidden" animate="visible" variants={containerVariants} className="mx-auto max-w-4xl text-center">
            <motion.div variants={itemVariants} className="mb-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary">
                <Icons.logoBrand className="h-4 w-4" />
                Reference Implementation
              </div>
            </motion.div>

            <motion.h1 variants={itemVariants} className="font-['Space_Grotesk'] text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Fullstack Python + <span className="bg-linear-to-r from-primary to-accent bg-clip-text text-transparent">React SPA</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
              A production-ready reference app built with Litestar, React 19, and modern tooling. Authentication, teams, background jobs, and admin dashboard included.
            </motion.p>

            <motion.div variants={itemVariants} className="mt-8 flex flex-wrap justify-center gap-4">
              <Button asChild size="lg" className="h-12 px-8">
                <Link to="/signup">
                  Try the demo
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 px-8">
                <a href="https://github.com/litestar-org/litestar-fullstack" target="_blank" rel="noopener noreferrer">
                  <Icons.gitHub className="mr-2 h-4 w-4" />
                  View source
                </a>
              </Button>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="border-b border-border/40 bg-muted/30">
        <div className="container mx-auto px-4 py-12">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
            variants={containerVariants}
            className="flex flex-wrap items-center justify-center gap-8 md:gap-12"
          >
            {techStack.map((tech) => (
              <motion.div key={tech.name} variants={itemVariants} className="group flex flex-col items-center gap-2">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-background shadow-sm ring-1 ring-border/50 transition-all group-hover:shadow-md group-hover:ring-primary/20">
                  <tech.icon className="h-8 w-8" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-foreground">{tech.name}</p>
                  <p className="text-xs text-muted-foreground">{tech.description}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={containerVariants} className="mb-12 text-center">
            <motion.h2 variants={itemVariants} className="font-['Space_Grotesk'] text-3xl font-bold text-foreground">
              What's included
            </motion.h2>
            <motion.p variants={itemVariants} className="mt-3 text-muted-foreground">
              Everything you need to build a production web application
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
            variants={containerVariants}
            className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          >
            {features.map((feature) => (
              <motion.div key={feature.title} variants={itemVariants}>
                <Card className="h-full border-border/60 bg-card/50 transition-colors hover:bg-card">
                  <CardContent className="p-6">
                    <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <feature.icon className="h-5 w-5" />
                    </div>
                    <h3 className="mb-3 font-semibold text-foreground">{feature.title}</h3>
                    <ul className="space-y-2">
                      {feature.items.map((item) => (
                        <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Check className="h-3.5 w-3.5 text-primary" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border/40 bg-muted/30 py-16">
        <div className="container mx-auto px-4">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="mx-auto max-w-2xl text-center">
            <h2 className="font-['Space_Grotesk'] text-2xl font-bold text-foreground sm:text-3xl">Try the live demo</h2>
            <p className="mt-3 text-muted-foreground">Create an account to explore teams, user management, background jobs, and the admin dashboard.</p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <Button asChild size="lg">
                <Link to="/signup">Create an account</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link to="/login">Sign in</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Icons.logoBrand className="h-6 w-6" />
              <span className="font-medium text-foreground">Litestar Fullstack</span>
            </div>
            <div className="flex gap-6">
              <Link to="/privacy" className="hover:text-foreground">
                Privacy
              </Link>
              <Link to="/terms" className="hover:text-foreground">
                Terms
              </Link>
              <Link to="/about" className="hover:text-foreground">
                About
              </Link>
              <a href="https://github.com/litestar-org/litestar-fullstack" target="_blank" rel="noopener noreferrer" className="hover:text-foreground">
                GitHub
              </a>
            </div>
          </div>
          <p className="mt-4 text-xs text-muted-foreground">© {new Date().getFullYear()} Litestar Organization. MIT License.</p>
        </div>
      </footer>
    </div>
  )
}
