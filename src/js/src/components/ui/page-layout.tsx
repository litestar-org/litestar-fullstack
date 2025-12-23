/**
 * Consistent page layout components for standardized spacing and animations
 */

import { motion } from "framer-motion"
import type * as React from "react"
import { cn } from "@/lib/utils"

interface PageContainerProps {
  children: React.ReactNode
  className?: string
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full"
}

const maxWidthClasses = {
  sm: "max-w-screen-sm",
  md: "max-w-screen-md",
  lg: "max-w-screen-lg",
  xl: "max-w-screen-xl",
  "2xl": "max-w-screen-2xl",
  full: "max-w-full",
}

export function PageContainer({ children, className, maxWidth = "2xl" }: PageContainerProps) {
  return <div className={cn("container mx-auto px-4 py-8 md:px-6 md:py-10", maxWidthClasses[maxWidth], className)}>{children}</div>
}

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  actions?: React.ReactNode
  className?: string
  animated?: boolean
}

export function PageHeader({ eyebrow, title, description, actions, className, animated = true }: PageHeaderProps) {
  const content = (
    <div className={cn("mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between", className)}>
      <div className="space-y-2">
        {eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">{eyebrow}</p>}
        <h1 className="font-['Space_Grotesk'] text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
        {description && <p className="max-w-2xl text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </div>
  )

  if (!animated) return content

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      {content}
    </motion.div>
  )
}

interface PageSectionProps {
  children: React.ReactNode
  className?: string
  delay?: number
  animated?: boolean
}

export function PageSection({ children, className, delay = 0, animated = true }: PageSectionProps) {
  if (!animated) {
    return <section className={cn("space-y-6", className)}>{children}</section>
  }

  return (
    <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.4 }} className={cn("space-y-6", className)}>
      {children}
    </motion.section>
  )
}

interface PageGridProps {
  children: React.ReactNode
  className?: string
  columns?: 1 | 2 | 3 | 4
}

const gridClasses = {
  1: "grid-cols-1",
  2: "grid-cols-1 md:grid-cols-2",
  3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
}

export function PageGrid({ children, className, columns = 3 }: PageGridProps) {
  return <div className={cn("grid gap-6", gridClasses[columns], className)}>{children}</div>
}

interface PageCardGridProps {
  children: React.ReactNode
  className?: string
  staggered?: boolean
}

export function PageCardGrid({ children, className, staggered = true }: PageCardGridProps) {
  if (!staggered) {
    return <div className={cn("grid gap-6 md:grid-cols-2 lg:grid-cols-3", className)}>{children}</div>
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: 0.1 },
        },
      }}
      className={cn("grid gap-6 md:grid-cols-2 lg:grid-cols-3", className)}
    >
      {children}
    </motion.div>
  )
}

export function PageCardGridItem({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 },
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

interface CenteredCardLayoutProps {
  children: React.ReactNode
  className?: string
}

export function CenteredCardLayout({ children, className }: CenteredCardLayoutProps) {
  return (
    <div className={cn("flex min-h-[calc(100vh-4rem)] items-center justify-center p-4", className)}>
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
        {children}
      </motion.div>
    </div>
  )
}
