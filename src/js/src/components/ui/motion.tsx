/**
 * Reusable Framer Motion animation wrappers and variants
 */

import { motion, type Variants } from "framer-motion"
import type * as React from "react"
import { cn } from "@/lib/utils"

// Animation Variants
export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
}

export const scaleOnHover: Variants = {
  initial: { scale: 1 },
  hover: { scale: 1.02 },
  tap: { scale: 0.98 },
}

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
}

export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0 },
}

export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: { opacity: 1, x: 0 },
}

// Spring transition presets
export const springTransition = {
  type: "spring" as const,
  stiffness: 400,
  damping: 17,
}

export const smoothTransition = {
  duration: 0.3,
  ease: [0.25, 0.1, 0.25, 1],
}

// Motion Components
interface MotionCardProps extends React.ComponentProps<typeof motion.div> {
  children: React.ReactNode
  className?: string
}

export function MotionCard({ children, className, ...props }: MotionCardProps) {
  return (
    <motion.div variants={scaleOnHover} initial="initial" whileHover="hover" whileTap="tap" transition={springTransition} className={cn("", className)} {...props}>
      {children}
    </motion.div>
  )
}

interface MotionSectionProps extends React.ComponentProps<typeof motion.section> {
  children: React.ReactNode
  className?: string
  delay?: number
}

export function MotionSection({ children, className, delay = 0, ...props }: MotionSectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.1, 0.25, 1] }}
      className={className}
      {...props}
    >
      {children}
    </motion.section>
  )
}

interface MotionFadeInProps extends React.ComponentProps<typeof motion.div> {
  children: React.ReactNode
  className?: string
  delay?: number
  direction?: "up" | "down" | "left" | "right" | "none"
}

export function MotionFadeIn({ children, className, delay = 0, direction = "up", ...props }: MotionFadeInProps) {
  const getInitial = () => {
    switch (direction) {
      case "up":
        return { opacity: 0, y: 20 }
      case "down":
        return { opacity: 0, y: -20 }
      case "left":
        return { opacity: 0, x: 20 }
      case "right":
        return { opacity: 0, x: -20 }
      case "none":
        return { opacity: 0 }
    }
  }

  return (
    <motion.div initial={getInitial()} animate={{ opacity: 1, x: 0, y: 0 }} transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }} className={className} {...props}>
      {children}
    </motion.div>
  )
}

interface MotionStaggerProps extends React.ComponentProps<typeof motion.div> {
  children: React.ReactNode
  className?: string
  staggerDelay?: number
}

export function MotionStagger({ children, className, staggerDelay = 0.1, ...props }: MotionStaggerProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: staggerDelay },
        },
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function MotionStaggerItem({ children, className, ...props }: MotionCardProps) {
  return (
    <motion.div variants={fadeInUp} transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }} className={className} {...props}>
      {children}
    </motion.div>
  )
}

// Floating animation for decorative elements
interface MotionFloatProps extends React.ComponentProps<typeof motion.div> {
  children: React.ReactNode
  className?: string
  duration?: number
  distance?: number
}

export function MotionFloat({ children, className, duration = 3, distance = 10, ...props }: MotionFloatProps) {
  return (
    <motion.div
      animate={{
        y: [-distance / 2, distance / 2, -distance / 2],
      }}
      transition={{
        duration,
        repeat: Number.POSITIVE_INFINITY,
        ease: "easeInOut",
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Glow pulse animation
interface MotionGlowProps extends React.ComponentProps<typeof motion.div> {
  children: React.ReactNode
  className?: string
}

export function MotionGlow({ children, className, ...props }: MotionGlowProps) {
  return (
    <motion.div
      animate={{
        boxShadow: ["0 0 20px hsl(43 81% 59% / 0.3)", "0 0 40px hsl(43 81% 59% / 0.5)", "0 0 20px hsl(43 81% 59% / 0.3)"],
      }}
      transition={{
        duration: 2,
        repeat: Number.POSITIVE_INFINITY,
        ease: "easeInOut",
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}
