import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Link } from "@tanstack/react-router"
import { motion } from "framer-motion"
import { ArrowRight, Lock, type LucideIcon, Rocket, Users } from "lucide-react"
import { useEffect, useState } from "react"

interface Feature {
  icon: LucideIcon
  title: string
  description: string
}

const features: Feature[] = [
  {
    icon: Rocket,
    title: "Fast & Efficient",
    description: "Built with performance in mind, ensuring smooth and responsive experience.",
  },
  {
    icon: Lock,
    title: "Secure & Reliable",
    description: "Enterprise-grade security to keep your data safe and protected.",
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description: "Seamless collaboration tools to keep your team in sync.",
  },
]

export function LandingPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Animation variants
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  }

  return (
    <div className="flex-1">
      <div className="h-full w-full bg-gradient-to-br from-background via-background to-primary/5">
        <div className="container relative mx-auto flex min-h-[calc(100vh-theme(spacing.16))] flex-col px-4 py-4">
          {/* Hero Section */}
          <div className="flex flex-grow items-center justify-center">
            <div className="flex flex-col items-center gap-8 md:flex-row">
              <div className="flex-1 text-center">
                <motion.h1
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="mb-6 bg-clip-text font-bold text-5xl md:text-6xl"
                >
                  Welcome to Litestar App
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                  className="mx-auto mb-8 max-w-xl text-muted-foreground text-xl"
                >
                  A powerful platform for team collaboration and project management. Join thousands of teams who are already using our platform to achieve their goals.
                </motion.p>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  className="flex flex-wrap justify-center gap-4"
                >
                  <Button asChild size="lg" className="rounded-full px-8 shadow-lg shadow-primary/20 transition-all hover:shadow-primary/30">
                    <Link to="/login">
                      Get Started <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                  <Button asChild variant="outline" size="lg" className="rounded-full px-8">
                    <Link to="/signup">Sign Up</Link>
                  </Button>
                </motion.div>
              </div>
            </div>
          </div>

          {/* Features Section */}
          {mounted && (
            <motion.div variants={container} initial="hidden" whileInView="show" viewport={{ once: true }} className="my-24 grid gap-8 md:grid-cols-3">
              {features.map((feature) => (
                <motion.div key={feature.title} variants={item}>
                  <Card className="h-full border-none bg-accent-foreground/10 p-6 shadow-lg backdrop-blur-sm transition-all duration-300 hover:shadow-xl">
                    <CardContent className="flex flex-col p-0">
                      <div className="mb-4 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
                        <feature.icon className="h-6 w-6 text-primary" />
                      </div>
                      <h3 className="mb-2 font-semibold text-xl">{feature.title}</h3>
                      <p className="text-muted-foreground">{feature.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          )}

          {/* CTA Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-16 rounded-3xl bg-gradient-to-r from-primary/10 to-primary/5 px-4 py-16 text-center shadow-lg backdrop-blur-sm md:px-16"
          >
            <h2 className="mb-4 font-bold text-3xl md:text-4xl">Ready to Get Started?</h2>
            <p className="mx-auto mb-8 max-w-lg text-muted-foreground">Join our community of successful teams today and transform the way you work.</p>
            <div className="flex flex-wrap justify-center gap-4">
              <Button asChild size="lg" variant="outline" className="rounded-full bg-background/80 px-8 hover:bg-background">
                <Link to="/login">Login</Link>
              </Button>
              <Button asChild size="lg" className="rounded-full px-8 shadow-lg shadow-primary/20 transition-all hover:shadow-primary/30">
                <Link to="/signup">
                  Sign Up <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </motion.div>

          {/* Footer Links */}
          <div className="border-border border-t pt-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="bg-clip-text font-bold text-2xl">Litestar</div>
              <div className="flex flex-wrap gap-8">
                <Link to="/privacy" className="text-muted-foreground text-sm transition-colors hover:text-foreground">
                  Privacy Policy
                </Link>
                <Link to="/terms" className="text-muted-foreground text-sm transition-colors hover:text-foreground">
                  Terms of Service
                </Link>
              </div>
            </div>
            <div className="text-center text-muted-foreground text-sm">© {new Date().getFullYear()} Litestar. All rights reserved.</div>
          </div>
        </div>
      </div>
    </div>
  )
}
