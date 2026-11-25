import { motion } from "framer-motion"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { getPasswordStrength, MAX_PASSWORD_STRENGTH_SCORE, type PasswordStrengthLevel } from "@/lib/validation"

const METER_COLORS: Record<PasswordStrengthLevel, string> = {
  weak: "bg-destructive",
  medium: "bg-warning",
  strong: "bg-success",
}

const LEVEL_TEXT_COLORS: Record<PasswordStrengthLevel, string> = {
  weak: "text-destructive",
  medium: "text-warning",
  strong: "text-success",
}

interface PasswordStrengthProps {
  password: string
  className?: string
}

/** Guidance while choosing a password. Nothing shown here blocks submission; the form schema and the server decide. */
export function PasswordStrength({ password, className }: Readonly<PasswordStrengthProps>) {
  if (!password) {
    return null
  }

  const { score, level, hasRequiredLength, characterClasses } = getPasswordStrength(password)
  const meterWidthPercent = (score / MAX_PASSWORD_STRENGTH_SCORE) * 100

  return (
    <div className={cn("space-y-3", className)}>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-medium text-foreground text-sm">Password strength</span>
          <span className={cn("font-medium text-sm capitalize", LEVEL_TEXT_COLORS[level])}>{level}</span>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            className={cn("h-2 rounded-full", METER_COLORS[level])}
            initial={{ width: 0 }}
            animate={{ width: `${meterWidthPercent}%` }}
            transition={{ type: "spring", stiffness: 100, damping: 15 }}
          />
        </div>
      </div>

      <div className="space-y-2">
        <span className="font-medium text-foreground text-sm">Required</span>
        <div className="grid grid-cols-1 gap-1">
          <ChecklistItem isMet={hasRequiredLength} text="12 to 128 characters" />
        </div>
      </div>

      <div className="space-y-2">
        <span className="font-medium text-foreground text-sm">A mix makes it stronger</span>
        <div className="grid grid-cols-1 gap-1">
          <ChecklistItem isMet={characterClasses.uppercase} text="Uppercase letters" />
          <ChecklistItem isMet={characterClasses.lowercase} text="Lowercase letters" />
          <ChecklistItem isMet={characterClasses.digits} text="Numbers" />
          <ChecklistItem isMet={characterClasses.symbols} text="Symbols (!@#$%^&*)" />
        </div>
      </div>
    </div>
  )
}

interface ChecklistItemProps {
  isMet: boolean
  text: string
}

function ChecklistItem({ isMet, text }: Readonly<ChecklistItemProps>) {
  return (
    <div className={cn("flex items-center space-x-2 text-sm transition-colors", isMet ? "text-success" : "text-muted-foreground")}>
      {isMet ? <Check className="h-4 w-4 shrink-0 text-success" /> : <div className="h-4 w-4 shrink-0 rounded-full border border-border" />}
      <span>{text}</span>
    </div>
  )
}
