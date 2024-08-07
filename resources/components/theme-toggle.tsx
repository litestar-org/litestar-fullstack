import { Button } from "@/components/ui/button"
import { useTheme } from "@/components/theme-provider"
import { cn } from "@/lib/utils"
import { MoonIcon, ServerIcon, SunIcon } from "lucide-react"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex items-center gap-x-1 [&_svg]:size-4 [&_button]:rounded-full">
      <Button
        size="icon"
        variant="ghost"
        className={cn(theme === "light" ? "bg-secondary" : "bg-background")}
        onClick={() => setTheme("light")}
      >
        <SunIcon />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className={cn(theme === "dark" ? "bg-secondary" : "bg-background")}
        onClick={() => setTheme("dark")}
      >
        <MoonIcon />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className={cn(theme === "system" ? "bg-secondary" : "bg-background")}
        onClick={() => setTheme("system")}
      >
        <ServerIcon />
      </Button>
    </div>
  )
}
