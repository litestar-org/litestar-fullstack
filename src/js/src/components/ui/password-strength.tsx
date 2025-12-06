/**
 * Password strength indicator component with visual feedback
 */

import { type PasswordStrength, getPasswordStrength } from "@/hooks/use-validation"
import { cn } from "@/lib/utils"
import { Check, X } from "lucide-react"

export interface PasswordStrengthProps {
  password: string
  showRequirements?: boolean
  className?: string
}

const strengthColors = {
  weak: "bg-red-500",
  medium: "bg-yellow-500",
  strong: "bg-green-500",
} as const

const strengthTextColors = {
  weak: "text-red-600",
  medium: "text-yellow-600",
  strong: "text-green-600",
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
          <span className="font-medium text-gray-700 text-sm">Password strength</span>
          <span className={cn("font-medium text-sm capitalize", strengthTextColors[strength.strength])}>{strength.strength}</span>
        </div>

        <div className="h-2 w-full rounded-full bg-gray-200">
          <div className={cn("h-2 rounded-full transition-all duration-300 ease-in-out", strengthColors[strength.strength])} style={{ width: `${progressWidth}%` }} />
        </div>
      </div>

      {/* Requirements checklist */}
      {showRequirements && (
        <div className="space-y-2">
          <span className="font-medium text-gray-700 text-sm">Requirements</span>
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
          {strength.feedback.map((message, index) => (
            <div key={index} className="flex items-center space-x-2 text-gray-600 text-sm">
              <X className="h-4 w-4 flex-shrink-0 text-red-400" />
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
    <div className={cn("flex items-center space-x-2 text-sm transition-colors", met ? "text-green-600" : "text-gray-500")}>
      {met ? <Check className="h-4 w-4 flex-shrink-0 text-green-600" /> : <div className="h-4 w-4 flex-shrink-0 rounded-full border border-gray-300" />}
      <span>{text}</span>
    </div>
  )
}

export default PasswordStrength
