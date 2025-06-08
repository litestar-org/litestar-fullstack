/**
 * Password strength indicator component with visual feedback
 */

import { type PasswordStrength, getPasswordStrength } from "@/hooks/use-validation"
import { cn } from "@/lib/utils"
import { CheckIcon, XMarkIcon } from "@heroicons/react/24/outline"
import React from "react"

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
          <span className="text-sm font-medium text-gray-700">Password strength</span>
          <span className={cn("text-sm font-medium capitalize", strengthTextColors[strength.strength])}>{strength.strength}</span>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className={cn("h-2 rounded-full transition-all duration-300 ease-in-out", strengthColors[strength.strength])} style={{ width: `${progressWidth}%` }} />
        </div>
      </div>

      {/* Requirements checklist */}
      {showRequirements && (
        <div className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Requirements</span>
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
            <div key={index} className="flex items-center space-x-2 text-sm text-gray-600">
              <XMarkIcon className="h-4 w-4 text-red-400 flex-shrink-0" />
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
      {met ? <CheckIcon className="h-4 w-4 text-green-600 flex-shrink-0" /> : <div className="h-4 w-4 rounded-full border border-gray-300 flex-shrink-0" />}
      <span>{text}</span>
    </div>
  )
}

export default PasswordStrength
