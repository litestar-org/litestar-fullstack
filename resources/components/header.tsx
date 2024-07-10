import * as React from "react"
import { cn } from "@/lib/utils"
import { Container } from "@/components/container"

const Header = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("py-4 bg-background sm:py-8 border-b mb-12", className)}
    {...props}
  >
    <Container>
      <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">
        {props.title}
      </h1>
    </Container>
  </div>
))
Header.displayName = "Header"

export { Header }
