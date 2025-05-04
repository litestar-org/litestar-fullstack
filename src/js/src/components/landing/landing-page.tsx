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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="container mx-auto px-4 py-4 relative flex flex-col min-h-[calc(100vh-theme(spacing.16))]">
        {/* Decorative elements */}
        <div className="absolute top-20 right-10 w-64 h-64 bg-primary/5 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-20 left-10 w-64 h-64 bg-primary/10 rounded-full blur-3xl -z-10" />

        {/* Hero Section */}
        <div className="flex flex-grow items-center justify-center">
          <div className="flex flex-col md:flex-row gap-8 items-center">
            <div className="flex-1 text-center">
              <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="text-5xl md:text-6xl font-bold mb-6 bg-clip-text">
                Welcome to Litestar App
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="text-xl text-muted-foreground mb-8 max-w-xl mx-auto"
              >
                A powerful platform for team collaboration and project management. Join thousands of teams who are already using our platform to achieve their goals.
              </motion.p>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="flex gap-4 flex-wrap justify-center">
                <Button asChild size="lg" className="rounded-full px-8 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all">
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
          <motion.div variants={container} initial="hidden" whileInView="show" viewport={{ once: true }} className="grid md:grid-cols-3 gap-8 my-24">
            {features.map((feature) => (
              <motion.div key={feature.title} variants={item}>
                <Card className="h-full border-none bg-accent-foreground/10 p-6 shadow-lg backdrop-blur-sm transition-all duration-300 hover:shadow-xl">
                  <CardContent className="p-0 flex flex-col">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4 flex-shrink-0">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
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
          className="text-center py-16 px-4 md:px-16 rounded-3xl bg-gradient-to-r from-primary/10 to-primary/5 backdrop-blur-sm shadow-lg mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-muted-foreground mb-8 max-w-lg mx-auto">Join our community of successful teams today and transform the way you work.</p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Button asChild size="lg" variant="outline" className="rounded-full px-8 bg-background/80 hover:bg-background">
              <Link to="/login">Login</Link>
            </Button>
            <Button asChild size="lg" className="rounded-full px-8 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all">
              <Link to="/signup">
                Sign Up <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </motion.div>

        {/* Footer Links */}
        <div className="pt-8 border-t border-border">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div className="text-2xl font-bold bg-clip-text">Litestar</div>
            <div className="flex flex-wrap gap-8">
              <Link to="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Terms of Service
              </Link>
            </div>
          </div>
          <div className="text-center text-sm text-muted-foreground">© {new Date().getFullYear()} Litestar. All rights reserved.</div>
        </div>
      </div>
    </div>
  )
}
