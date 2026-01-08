/**
 * Password strength indicator component with visual feedback
 */

import { motion } from "framer-motion"
import { Check, X } from "lucide-react"
import { getPasswordStrength } from "@/hooks/use-validation"
import { cn } from "@/lib/utils"

export interface PasswordStrengthProps {
  password: string
  showRequirements?: boolean
  className?: string
}

const strengthColors = {
  weak: "bg-destructive",
  medium: "bg-warning",
  strong: "bg-success",
} as const

const strengthTextColors = {
  weak: "text-destructive",
  medium: "text-warning",
  strong: "text-success",
} as const

export function PasswordStrength({ password, showRequirements = true, className }: PasswordStrengthProps) {
  const strength = getPasswordStrength(password)
  const progressWidth = password ? (strength.score / 8) * 100 : 0

  // Don't show anything if password is empty
  if (!password) {
    return null
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Strength meter */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-medium text-foreground text-sm">Password strength</span>
          <span className={cn("font-medium text-sm capitalize", strengthTextColors[strength.strength])}>{strength.strength}</span>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            className={cn("h-2 rounded-full", strengthColors[strength.strength])}
            initial={{ width: 0 }}
            animate={{ width: `${progressWidth}%` }}
            transition={{ type: "spring", stiffness: 100, damping: 15 }}
          />
        </div>
      </div>

      {/* Requirements checklist */}
      {showRequirements && (
        <div className="space-y-2">
          <span className="font-medium text-foreground text-sm">Requirements</span>
          <div className="grid grid-cols-1 gap-1">
            <RequirementItem met={strength.requirements.length} text="At least 12 characters" />
            <RequirementItem met={strength.requirements.uppercase} text="One uppercase letter" />
            <RequirementItem met={strength.requirements.lowercase} text="One lowercase letter" />
            <RequirementItem met={strength.requirements.digits} text="One number" />
            <RequirementItem met={strength.requirements.special} text="One special character (!@#$%^&*)" />
            <RequirementItem met={strength.requirements.notCommon} text="Not a common password" />
          </div>
        </div>
      )}

      {/* Feedback messages */}
      {strength.feedback.length > 0 && (
        <div className="space-y-1">
          {strength.feedback.map((message) => (
            <div key={message} className="flex items-center space-x-2 text-muted-foreground text-sm">
              <X className="h-4 w-4 shrink-0 text-destructive" />
              <span>{message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface RequirementItemProps {
  met: boolean
  text: string
}

function RequirementItem({ met, text }: RequirementItemProps) {
  return (
    <div className={cn("flex items-center space-x-2 text-sm transition-colors", met ? "text-success" : "text-muted-foreground")}>
      {met ? <Check className="h-4 w-4 shrink-0 text-success" /> : <div className="h-4 w-4 shrink-0 rounded-full border border-border" />}
      <span>{text}</span>
    </div>
  )
}

export default PasswordStrength
