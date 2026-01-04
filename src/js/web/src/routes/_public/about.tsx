import { createFileRoute, Link } from "@tanstack/react-router"
import { motion, useMotionValue, useTransform } from "framer-motion"
import { ArrowLeft, Github, Heart, Star, Zap } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { PageContainer, PageHeader } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_public/about")({
  component: AboutPage,
})

// Konami code sequence
const KONAMI_CODE = ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown", "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight", "b", "a"]

const teamMembers = [
  { name: "Litestar Team", role: "Core Maintainers", avatar: "L" },
  { name: "Community", role: "Contributors", avatar: "C" },
  { name: "You", role: "Builder", avatar: "Y" },
]

const features = [
  { icon: Zap, title: "High Performance", description: "Built for speed with async-first architecture" },
  { icon: Star, title: "Type Safety", description: "End-to-end typing from Python to React" },
  { icon: Heart, title: "Developer Experience", description: "Intuitive APIs and excellent documentation" },
]

function AboutPage() {
  const [easterEggActive, setEasterEggActive] = useState(false)
  const [konamiIndex, setKonamiIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  // Cursor-following gradient
  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const rect = containerRef.current?.getBoundingClientRect()
      if (rect) {
        mouseX.set(e.clientX - rect.left)
        mouseY.set(e.clientY - rect.top)
      }
    },
    [mouseX, mouseY],
  )

  const gradientX = useTransform(mouseX, [0, 800], [0, 100])
  const gradientY = useTransform(mouseY, [0, 600], [0, 100])

  // Konami code listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (easterEggActive) {
        setEasterEggActive(false)
        return
      }

      const key = e.key
      const expectedKey = KONAMI_CODE[konamiIndex]

      if (key === expectedKey) {
        const nextIndex = konamiIndex + 1
        if (nextIndex === KONAMI_CODE.length) {
          setEasterEggActive(true)
          setKonamiIndex(0)
        } else {
          setKonamiIndex(nextIndex)
        }
      } else {
        setKonamiIndex(0)
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [konamiIndex, easterEggActive])

  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: Visual-only mouse tracker for cursor-following gradient effect
    <div ref={containerRef} onMouseMove={handleMouseMove} role="presentation" className="relative min-h-screen">
      {/* Easter egg overlay */}
      {easterEggActive && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-brand-navy"
          onClick={() => setEasterEggActive(false)}
        >
          {/* Animated star constellation */}
          <div className="relative">
            {/* Orbiting particles */}
            {Array.from({ length: 12 }).map((_, i) => (
              <motion.div
                key={`star-${i}-${Math.random()}`}
                initial={{ opacity: 0, scale: 0 }}
                animate={{
                  opacity: [0, 1, 0],
                  scale: [0, 1, 0],
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 3,
                  repeat: Number.POSITIVE_INFINITY,
                  delay: i * 0.25,
                  ease: "easeInOut",
                }}
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "50%",
                  x: Math.cos((i / 12) * Math.PI * 2) * 150 - 6,
                  y: Math.sin((i / 12) * Math.PI * 2) * 150 - 6,
                }}
                className="h-3 w-3 rounded-full bg-primary shadow-glow-sm"
              />
            ))}

            {/* Central glowing logo */}
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                rotate: [0, 360],
              }}
              transition={{
                scale: { duration: 2, repeat: Number.POSITIVE_INFINITY },
                rotate: { duration: 20, repeat: Number.POSITIVE_INFINITY, ease: "linear" },
              }}
              className="relative flex h-32 w-32 items-center justify-center rounded-full bg-primary/20 shadow-glow-lg backdrop-blur"
            >
              <Star className="h-16 w-16 text-primary" />
            </motion.div>

            {/* Celebration text */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="absolute -bottom-20 left-1/2 -translate-x-1/2 whitespace-nowrap text-center text-lg font-semibold text-primary"
            >
              You found the secret!
            </motion.p>
          </div>

          <p className="absolute bottom-10 text-center text-sm text-muted-foreground">Press any key to exit</p>
        </motion.div>
      )}

      {/* Cursor-following glow effect */}
      <motion.div
        style={{
          background: `radial-gradient(circle at ${gradientX.get()}% ${gradientY.get()}%, hsl(var(--primary) / 0.1), transparent 50%)`,
        }}
        className="pointer-events-none absolute inset-0"
      />

      <PageContainer className="relative">
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/landing">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to home
            </Link>
          </Button>
        </div>

        <PageHeader eyebrow="About" title="The Litestar Fullstack Project" description="A production-grade reference implementation for modern Python web applications." />

        {/* Features grid */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
          }}
          className="mb-12 grid gap-6 md:grid-cols-3"
        >
          {features.map((feature) => (
            <motion.div key={feature.title} variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
              <Card hover glow className="h-full">
                <CardContent className="space-y-3 p-6">
                  <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    transition={{ type: "spring", stiffness: 400, damping: 17 }}
                    className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/15 text-primary"
                  >
                    <feature.icon className="h-6 w-6" />
                  </motion.div>
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Team section */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold">Built by the Community</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {teamMembers.map((member, index) => (
              <motion.div key={member.name} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.4 + index * 0.1 }}>
                <Card hover className="text-center">
                  <CardContent className="p-6">
                    <motion.div
                      whileHover={{ scale: 1.1 }}
                      className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/20 text-2xl font-bold text-primary"
                    >
                      {member.avatar}
                    </motion.div>
                    <h3 className="font-semibold">{member.name}</h3>
                    <p className="text-sm text-muted-foreground">{member.role}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Links */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="flex flex-wrap justify-center gap-4">
          <Button variant="outline" asChild>
            <a href="https://github.com/litestar-org" target="_blank" rel="noopener noreferrer">
              <Github className="mr-2 h-4 w-4" /> GitHub
            </a>
          </Button>
          <Button variant="outline" asChild>
            <a href="https://litestar.dev" target="_blank" rel="noopener noreferrer">
              Documentation
            </a>
          </Button>
        </motion.div>

        {/* Hidden hint */}
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }} className="mt-16 text-center text-xs text-muted-foreground/40">
          Try the classic code...
        </motion.p>
      </PageContainer>
    </div>
  )
}
