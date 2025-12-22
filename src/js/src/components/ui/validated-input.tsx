/**
 * Validated input component with real-time validation feedback
 */

import { Eye, EyeOff } from "lucide-react"
import type React from "react"
import { useEffect, useRef, useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { PasswordStrength } from "@/components/ui/password-strength"
import type { ValidationRule } from "@/hooks/use-validation"
import { cn } from "@/lib/utils"

export interface ValidatedInputProps extends Omit<React.ComponentProps<"input">, "onChange"> {
  label: string
  error?: string
  validationRule?: ValidationRule
  showPasswordStrength?: boolean
  validateOnBlur?: boolean
  validateOnChange?: boolean
  debounceMs?: number
  onChange?: (value: string, isValid: boolean) => void
  onValidationChange?: (error: string | null) => void
  helperText?: string
}

export function ValidatedInput({
  label,
  error: externalError,
  validationRule,
  showPasswordStrength = false,
  validateOnBlur = true,
  validateOnChange = true,
  debounceMs = 300,
  onChange,
  onValidationChange,
  helperText,
  type = "text",
  className,
  ...props
}: ValidatedInputProps) {
  const [value, setValue] = useState(props.value?.toString() || "")
  const [internalError, setInternalError] = useState<string>("")
  const [showPassword, setShowPassword] = useState(false)
  const [hasBeenBlurred, setHasBeenBlurred] = useState(false)
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  // Use external error if provided, otherwise use internal error
  const displayError = externalError || internalError
  const isPassword = type === "password"
  const actualType = isPassword && showPassword ? "text" : type

  // Validation function
  const validateValue = (val: string): string | null => {
    if (!validationRule) return null

    // Required validation
    if (validationRule.required && !val.trim()) {
      return "This field is required"
    }

    // Skip other validations if field is empty and not required
    if (!val.trim() && !validationRule.required) {
      return null
    }

    // Min length
    if (validationRule.minLength && val.length < validationRule.minLength) {
      return `Must be at least ${validationRule.minLength} characters`
    }

    // Max length
    if (validationRule.maxLength && val.length > validationRule.maxLength) {
      return `Must not exceed ${validationRule.maxLength} characters`
    }

    // Pattern validation
    if (validationRule.pattern && !validationRule.pattern.test(val)) {
      return "Invalid format"
    }

    // Custom validation
    if (validationRule.custom) {
      return validationRule.custom(val)
    }

    return null
  }

  // Debounced validation
  const debouncedValidate = (val: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(() => {
      const error = validateValue(val)
      setInternalError(error || "")
      onValidationChange?.(error)
    }, debounceMs)
  }

  // Handle value change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setValue(newValue)

    // Immediate callback for parent component
    const error = validateValue(newValue)
    onChange?.(newValue, !error)

    // Real-time validation (debounced)
    if (validateOnChange && (hasBeenBlurred || newValue === "")) {
      debouncedValidate(newValue)
    }
  }

  // Handle blur
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setHasBeenBlurred(true)

    if (validateOnBlur) {
      const error = validateValue(value)
      setInternalError(error || "")
      onValidationChange?.(error)
    }

    props.onBlur?.(e)
  }

  // Clean up debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [])

  // Sync external value changes
  useEffect(() => {
    if (props.value !== undefined) {
      setValue(props.value.toString())
    }
  }, [props.value])

  const inputId = props.id || `input-${label.toLowerCase().replace(/\s+/g, "-")}`

  return (
    <div className="space-y-2">
      {/* Label */}
      <Label htmlFor={inputId} className="font-medium text-foreground text-sm">
        {label}
        {validationRule?.required && <span className="ml-1 text-red-500">*</span>}
      </Label>

      {/* Input wrapper */}
      <div className="relative">
        <Input
          {...props}
          id={inputId}
          type={actualType}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          className={cn(displayError && "border-red-500 focus:border-red-500 focus:ring-red-500", isPassword && "pr-10", className)}
          aria-invalid={!!displayError}
          aria-describedby={displayError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        />

        {/* Password toggle */}
        {isPassword && (
          <button
            type="button"
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground"
            onClick={() => setShowPassword(!showPassword)}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        )}
      </div>

      {/* Error message */}
      {displayError && (
        <p id={`${inputId}-error`} className="text-red-600 text-sm" role="alert">
          {displayError}
        </p>
      )}

      {/* Helper text */}
      {!displayError && helperText && (
        <p id={`${inputId}-helper`} className="text-muted-foreground text-sm">
          {helperText}
        </p>
      )}

      {/* Password strength indicator */}
      {showPasswordStrength && isPassword && value && (
        <div className="mt-3">
          <PasswordStrength password={value} />
        </div>
      )}
    </div>
  )
}

export default ValidatedInput
