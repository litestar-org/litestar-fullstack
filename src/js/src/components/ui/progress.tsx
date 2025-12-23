import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cva, type VariantProps } from "class-variance-authority"
import { motion, useSpring, useTransform } from "framer-motion"
import * as React from "react"

import { cn } from "@/lib/utils"

const progressVariants = cva("h-full w-full flex-1 transition-colors", {
  variants: {
    variant: {
      default: "bg-primary",
      success: "bg-success",
      warning: "bg-warning",
      destructive: "bg-destructive",
      info: "bg-info",
    },
  },
  defaultVariants: {
    variant: "default",
  },
})

interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>, VariantProps<typeof progressVariants> {
  showValue?: boolean
  animated?: boolean
}

const Progress = React.forwardRef<React.ElementRef<typeof ProgressPrimitive.Root>, ProgressProps>(
  ({ className, value, variant, showValue = false, animated = true, ...props }, ref) => {
    // Normalize value to always be a number
    const normalizedValue = value ?? 0

    // Spring animation for smooth value transitions
    const springValue = useSpring(normalizedValue, {
      stiffness: 100,
      damping: 20,
      mass: 0.5,
    })

    // Update spring when value changes
    React.useEffect(() => {
      springValue.set(normalizedValue)
    }, [normalizedValue, springValue])

    const translateX = useTransform(springValue, (v) => `translateX(-${100 - v}%)`)

    return (
      <div className={cn("relative", showValue && "flex items-center gap-3")}>
        <ProgressPrimitive.Root ref={ref} value={normalizedValue} className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)} {...props}>
          {animated ? (
            <motion.div className={cn(progressVariants({ variant }), "rounded-full")} style={{ transform: translateX }} />
          ) : (
            <ProgressPrimitive.Indicator className={cn(progressVariants({ variant }), "rounded-full transition-transform")} style={{ transform: `translateX(-${100 - normalizedValue}%)` }} />
          )}
        </ProgressPrimitive.Root>
        {showValue && <span className="min-w-[3ch] text-right text-sm font-medium tabular-nums text-muted-foreground">{Math.round(normalizedValue)}%</span>}
      </div>
    )
  },
)
Progress.displayName = ProgressPrimitive.Root.displayName

/**
 * Indeterminate progress bar with sliding animation
 */
interface ProgressIndeterminateProps extends VariantProps<typeof progressVariants> {
  className?: string
}

function ProgressIndeterminate({ className, variant }: ProgressIndeterminateProps) {
  return (
    <div className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}>
      <motion.div
        className={cn(progressVariants({ variant }), "absolute h-full w-1/3 rounded-full")}
        animate={{
          x: ["-100%", "400%"],
        }}
        transition={{
          duration: 1.5,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
        }}
      />
    </div>
  )
}

/**
 * Circular progress indicator
 */
interface ProgressCircularProps extends VariantProps<typeof progressVariants> {
  value?: number
  size?: "sm" | "md" | "lg"
  showValue?: boolean
  className?: string
}

const sizeMap = {
  sm: { size: 32, strokeWidth: 3, fontSize: "text-[10px]" },
  md: { size: 48, strokeWidth: 4, fontSize: "text-xs" },
  lg: { size: 64, strokeWidth: 5, fontSize: "text-sm" },
}

const variantStrokeColors = {
  default: "stroke-primary",
  success: "stroke-success",
  warning: "stroke-warning",
  destructive: "stroke-destructive",
  info: "stroke-info",
}

function ProgressCircular({ value = 0, size = "md", variant = "default", showValue = false, className }: ProgressCircularProps) {
  const { size: svgSize, strokeWidth, fontSize } = sizeMap[size]
  const radius = (svgSize - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI

  const springValue = useSpring(value, {
    stiffness: 100,
    damping: 20,
    mass: 0.5,
  })

  React.useEffect(() => {
    springValue.set(value)
  }, [value, springValue])

  const strokeDashoffset = useTransform(springValue, (v) => circumference - (v / 100) * circumference)

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`} className="-rotate-90">
        {/* Background circle */}
        <circle cx={svgSize / 2} cy={svgSize / 2} r={radius} fill="none" strokeWidth={strokeWidth} className="stroke-secondary" />
        {/* Progress circle */}
        <motion.circle
          cx={svgSize / 2}
          cy={svgSize / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className={variantStrokeColors[variant || "default"]}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset,
          }}
        />
      </svg>
      {showValue && <span className={cn("absolute font-medium tabular-nums text-foreground", fontSize)}>{Math.round(value)}%</span>}
    </div>
  )
}

/**
 * Circular indeterminate spinner
 */
interface ProgressSpinnerProps extends VariantProps<typeof progressVariants> {
  size?: "sm" | "md" | "lg"
  className?: string
}

function ProgressSpinner({ size = "md", variant = "default", className }: ProgressSpinnerProps) {
  const { size: svgSize, strokeWidth } = sizeMap[size]
  const radius = (svgSize - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <motion.svg
        width={svgSize}
        height={svgSize}
        viewBox={`0 0 ${svgSize} ${svgSize}`}
        animate={{ rotate: 360 }}
        transition={{
          duration: 1,
          repeat: Number.POSITIVE_INFINITY,
          ease: "linear",
        }}
      >
        <circle cx={svgSize / 2} cy={svgSize / 2} r={radius} fill="none" strokeWidth={strokeWidth} className="stroke-secondary" />
        <circle
          cx={svgSize / 2}
          cy={svgSize / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className={variantStrokeColors[variant || "default"]}
          style={{
            strokeDasharray: `${circumference * 0.25} ${circumference * 0.75}`,
          }}
        />
      </motion.svg>
    </div>
  )
}

export { Progress, ProgressIndeterminate, ProgressCircular, ProgressSpinner, progressVariants }
