import { motion } from "framer-motion"
import { Check, X } from "lucide-react"
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

export function PasswordStrength({ password, className }: Readonly<PasswordStrengthProps>) {
  if (!password) {
    return null
  }

  const { score, level, requirements, feedback } = getPasswordStrength(password)
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
        <span className="font-medium text-foreground text-sm">Requirements</span>
        <div className="grid grid-cols-1 gap-1">
          <RequirementItem isMet={requirements.length} text="At least 12 characters" />
          <RequirementItem isMet={requirements.uppercase} text="One uppercase letter" />
          <RequirementItem isMet={requirements.lowercase} text="One lowercase letter" />
          <RequirementItem isMet={requirements.digits} text="One number" />
          <RequirementItem isMet={requirements.special} text="One special character (!@#$%^&*)" />
          <RequirementItem isMet={requirements.notCommon} text="Not a common password" />
        </div>
      </div>

      {feedback.length > 0 && (
        <div className="space-y-1">
          {feedback.map((hint) => (
            <div key={hint} className="flex items-center space-x-2 text-muted-foreground text-sm">
              <X className="h-4 w-4 shrink-0 text-destructive" />
              <span>{hint}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface RequirementItemProps {
  isMet: boolean
  text: string
}

function RequirementItem({ isMet, text }: Readonly<RequirementItemProps>) {
  return (
    <div className={cn("flex items-center space-x-2 text-sm transition-colors", isMet ? "text-success" : "text-muted-foreground")}>
      {isMet ? <Check className="h-4 w-4 shrink-0 text-success" /> : <div className="h-4 w-4 shrink-0 rounded-full border border-border" />}
      <span>{text}</span>
    </div>
  )
}
