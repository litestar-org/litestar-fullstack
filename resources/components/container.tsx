import * as React from "react"
import { cn } from "@/lib/utils"

const Container = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("px-4 sm:px-6 mx-auto max-w-7xl", className)}
    {...props}
  />
))
Container.displayName = "Container"

export { Container }
