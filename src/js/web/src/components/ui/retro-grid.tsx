import { cn } from "@/lib/utils"

interface RetroGridProps {
  className?: string
  angle?: number
}

export function RetroGrid({ className, angle = 65 }: RetroGridProps) {
  return (
    <div
      className={cn("pointer-events-none absolute inset-0 overflow-hidden opacity-60 [perspective:200px]", className)}
      style={{ "--grid-angle": `${angle}deg` } as React.CSSProperties}
    >
      {/* Stars */}
      <div
        className="absolute inset-0 opacity-70 animate-star-drift motion-reduce:animate-none"
        style={{
          backgroundImage: [
            "radial-gradient(2px 2px at 15% 20%, var(--grid-star) 0, transparent 60%)",
            "radial-gradient(1.5px 1.5px at 35% 12%, var(--grid-star) 0, transparent 60%)",
            "radial-gradient(1.5px 1.5px at 65% 18%, var(--grid-star) 0, transparent 60%)",
            "radial-gradient(2px 2px at 82% 26%, var(--grid-star) 0, transparent 60%)",
            "radial-gradient(1.5px 1.5px at 55% 32%, var(--grid-star) 0, transparent 60%)",
          ].join(","),
        }}
      />

      {/* Grid */}
      <div className="absolute inset-0 [transform:rotateX(var(--grid-angle))]">
        <div
          className={cn(
            "animate-grid motion-reduce:animate-none",
            "[background-repeat:repeat] [background-size:60px_60px] [height:300vh] [inset:0%_0px] [margin-left:-50%] [transform-origin:100%_0_0] [width:600vw]",
            "[background-image:linear-gradient(to_right,var(--grid-line-strong)_1px,transparent_0),linear-gradient(to_bottom,var(--grid-line)_1px,transparent_0)]",
          )}
        />
        <div
          className={cn(
            "animate-grid motion-reduce:animate-none",
            "opacity-40 [background-repeat:repeat] [background-size:90px_90px] [height:240vh] [inset:0%_0px] [margin-left:-45%] [transform-origin:100%_0_0] [width:520vw]",
            "[background-image:linear-gradient(to_right,var(--grid-line)_1px,transparent_0),linear-gradient(to_bottom,var(--grid-line)_1px,transparent_0)]",
          )}
          style={{ animationDuration: "22s" }}
        />
      </div>

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-linear-to-t from-background via-background/50 to-transparent to-90%" />

      {/* Horizon glow */}
      <div className="absolute inset-x-0 bottom-24 h-24 bg-[radial-gradient(ellipse_at_center,var(--grid-glow)_0%,transparent_70%)]" />

      {/* Vignette + noise */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_45%,rgba(0,0,0,0.28)_100%)]" />
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 80 80'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='80' height='80' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E\")",
          mixBlendMode: "soft-light",
        }}
      />
    </div>
  )
}
