/**
 * React hook for form validation with real-time feedback
 */

import { useCallback, useState } from "react"

// Validation rule types
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => string | null
}

export interface ValidationRules {
  [field: string]: ValidationRule
}

export interface ValidationResult {
  errors: Record<string, string>
  isValid: boolean
  validate: (field?: string) => boolean
  validateField: (field: string, value: any) => string | null
  clearErrors: (field?: string) => void
}

// Email validation constants (matching backend)
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$/
const EMAIL_DOUBLE_DOT_REGEX = /\.\.+/
const EMAIL_BLOCKED_DOMAINS = ["10minutemail.com", "tempmail.org", "guerrillamail.com", "mailinator.com", "throwaway.email", "temp-mail.org", "yopmail.com", "maildrop.cc"]
const EMAIL_BLOCKED_PATTERNS = [/.*\+.*test.*@.*/, /.*\+.*spam.*@.*/, /^test.*@.*/, /^noreply@.*/, /^no-reply@.*/]

// Password validation constants (matching backend)
const PASSWORD_MIN_LENGTH = 12
const PASSWORD_MAX_LENGTH = 128
const PASSWORD_UPPERCASE_REGEX = /[A-Z]/
const PASSWORD_LOWERCASE_REGEX = /[a-z]/
const PASSWORD_DIGIT_REGEX = /\d/
const PASSWORD_SPECIAL_REGEX = /[!@#$%^&*(),.?":{}|<>_+=\-[\]\\/~`]/
const PASSWORD_COMMON_PATTERNS = [/password/i, /123456/, /qwerty/i, /admin/i]
const PASSWORD_REPEATED_REGEX = /(.)\1{4,}/
const PASSWORD_SEQUENTIAL_REGEX = /^(012|123|234|345|456|567|678|789|890|abc|bcd|cde)/i
const PASSWORD_KEYBOARD_REGEX = /^(qwe|asd|zxc)/i

// Username validation constants (matching backend)
const USERNAME_MIN_LENGTH = 3
const USERNAME_MAX_LENGTH = 30
const USERNAME_VALID_REGEX = /^[a-z0-9_-]+$/
const USERNAME_START_REGEX = /^[a-z0-9]/
const USERNAME_REPEATED_REGEX = /(.)\1{3,}/
const RESERVED_USERNAMES = [
  "admin",
  "root",
  "api",
  "www",
  "mail",
  "ftp",
  "support",
  "help",
  "security",
  "privacy",
  "terms",
  "about",
  "contact",
  "blog",
  "news",
  "app",
  "application",
  "system",
  "test",
  "user",
  "guest",
  "demo",
  "null",
  "undefined",
  "none",
]

// Phone validation constants (matching backend)
const PHONE_BASIC_REGEX = /^[+]?[0-9\s\-().]+$/
const PHONE_MIN_DIGITS = 7
const PHONE_MAX_DIGITS = 15

// Built-in validation functions
export const validateEmail = (email: string): string | null => {
  if (!email) return null

  const cleanEmail = email.trim().toLowerCase()

  // Length check
  if (cleanEmail.length > 254) return "Email address too long"
  if (cleanEmail.length < 3) return "Email address too short"

  // Basic format check
  if (!EMAIL_REGEX.test(cleanEmail)) return "Invalid email format"

  // Double dots check
  if (EMAIL_DOUBLE_DOT_REGEX.test(cleanEmail)) return "Invalid email format"

  // Check blocked domains
  const domain = cleanEmail.split("@")[1]
  if (EMAIL_BLOCKED_DOMAINS.includes(domain)) {
    return "This email domain is not allowed"
  }

  // Check blocked patterns
  for (const pattern of EMAIL_BLOCKED_PATTERNS) {
    if (pattern.test(cleanEmail)) {
      return "This email format is not allowed"
    }
  }

  // Local part length check
  const localPart = cleanEmail.split("@")[0]
  if (localPart.length > 64) return "Email local part too long"

  return null
}

export interface PasswordStrength {
  score: number
  strength: "weak" | "medium" | "strong"
  requirements: {
    length: boolean
    uppercase: boolean
    lowercase: boolean
    digits: boolean
    special: boolean
    notCommon: boolean
  }
  feedback: string[]
}

export const validatePassword = (password: string): string | null => {
  if (!password) return null

  // Length requirements
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters long`
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `Password must not exceed ${PASSWORD_MAX_LENGTH} characters`
  }

  // Character requirements
  if (!PASSWORD_UPPERCASE_REGEX.test(password)) {
    return "Password must contain at least one uppercase letter"
  }
  if (!PASSWORD_LOWERCASE_REGEX.test(password)) {
    return "Password must contain at least one lowercase letter"
  }
  if (!PASSWORD_DIGIT_REGEX.test(password)) {
    return "Password must contain at least one digit"
  }
  if (!PASSWORD_SPECIAL_REGEX.test(password)) {
    return "Password must contain at least one special character"
  }

  // Common pattern checks
  for (const pattern of PASSWORD_COMMON_PATTERNS) {
    if (pattern.test(password)) {
      return "Password is too common - please choose a more unique password"
    }
  }

  // Repeated characters
  if (PASSWORD_REPEATED_REGEX.test(password)) {
    return "Password is too common - please choose a more unique password"
  }

  // Sequential patterns
  if (PASSWORD_SEQUENTIAL_REGEX.test(password)) {
    return "Password is too common - please choose a more unique password"
  }

  // Keyboard patterns
  if (PASSWORD_KEYBOARD_REGEX.test(password)) {
    return "Password is too common - please choose a more unique password"
  }

  return null
}

export const getPasswordStrength = (password: string): PasswordStrength => {
  const requirements = {
    length: password.length >= PASSWORD_MIN_LENGTH,
    uppercase: PASSWORD_UPPERCASE_REGEX.test(password),
    lowercase: PASSWORD_LOWERCASE_REGEX.test(password),
    digits: PASSWORD_DIGIT_REGEX.test(password),
    special: PASSWORD_SPECIAL_REGEX.test(password),
    notCommon:
      !PASSWORD_COMMON_PATTERNS.some((p) => p.test(password)) &&
      !PASSWORD_REPEATED_REGEX.test(password) &&
      !PASSWORD_SEQUENTIAL_REGEX.test(password) &&
      !PASSWORD_KEYBOARD_REGEX.test(password),
  }

  const feedback: string[] = []
  let score = 0

  // Calculate score and feedback
  if (requirements.length) {
    score += 2
  } else {
    feedback.push("Use at least 12 characters")
  }

  if (requirements.uppercase) {
    score += 1
  } else {
    feedback.push("Include uppercase letters")
  }

  if (requirements.lowercase) {
    score += 1
  } else {
    feedback.push("Include lowercase letters")
  }

  if (requirements.digits) {
    score += 1
  } else {
    feedback.push("Include numbers")
  }

  if (requirements.special) {
    score += 1
  } else {
    feedback.push("Include special characters (!@#$%^&*)")
  }

  if (requirements.notCommon) {
    score += 1
  } else {
    feedback.push("Avoid common passwords")
  }

  // Bonus points for length
  if (password.length >= 16) score += 1
  if (password.length >= 20) score += 1

  // Determine strength level
  let strength: "weak" | "medium" | "strong"
  if (score >= 7) {
    strength = "strong"
  } else if (score >= 5) {
    strength = "medium"
  } else {
    strength = "weak"
  }

  return {
    score,
    strength,
    requirements,
    feedback,
  }
}

export const validateUsername = (username: string): string | null => {
  if (!username) return null

  const cleanUsername = username.trim().toLowerCase()

  // Length validation
  if (cleanUsername.length < USERNAME_MIN_LENGTH) {
    return `Username must be at least ${USERNAME_MIN_LENGTH} characters`
  }
  if (cleanUsername.length > USERNAME_MAX_LENGTH) {
    return `Username must not exceed ${USERNAME_MAX_LENGTH} characters`
  }

  // Character validation
  if (!USERNAME_VALID_REGEX.test(cleanUsername)) {
    return "Username can only contain letters, numbers, hyphens, and underscores"
  }

  // Must start with letter or number
  if (!USERNAME_START_REGEX.test(cleanUsername)) {
    return "Username must start with a letter or number"
  }

  // Check reserved usernames
  if (RESERVED_USERNAMES.includes(cleanUsername)) {
    return "Username is reserved and cannot be used"
  }

  // Abuse patterns
  if (USERNAME_REPEATED_REGEX.test(cleanUsername)) {
    return "Username contains too many repeated characters"
  }

  return null
}

export const validatePhone = (phone: string): string | null => {
  if (!phone) return null

  const cleanPhone = phone.trim()

  // Basic format validation
  if (!PHONE_BASIC_REGEX.test(cleanPhone)) {
    return "Invalid phone number format"
  }

  // Length validation (count digits only)
  const digitsOnly = cleanPhone.replace(/[^\d]/g, "")
  if (digitsOnly.length < PHONE_MIN_DIGITS || digitsOnly.length > PHONE_MAX_DIGITS) {
    return `Phone number must be between ${PHONE_MIN_DIGITS} and ${PHONE_MAX_DIGITS} digits`
  }

  return null
}

export const validateName = (name: string): string | null => {
  if (!name) return null

  const cleanName = name.trim().replace(/\s+/g, " ")

  // Length validation
  if (cleanName.length < 1) return "Name cannot be empty"
  if (cleanName.length > 100) return "Name must not exceed 100 characters"

  // Character validation - allow letters, spaces, hyphens, apostrophes, periods
  const nameRegex = /^[a-zA-ZÀ-ÿĀ-žА-я\u4e00-\u9fff\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\s'\-.]+$/
  if (!nameRegex.test(cleanName)) {
    return "Name contains invalid characters"
  }

  // Abuse patterns
  if (/(.)\1{4,}/.test(cleanName)) {
    return "Name contains suspicious patterns"
  }

  return null
}

/**
 * Main validation hook
 */
export function useValidation<T extends Record<string, any>>(data: T, rules: ValidationRules): ValidationResult {
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateField = useCallback(
    (field: string, value: any): string | null => {
      const rule = rules[field]
      if (!rule) return null

      // Required validation
      if (rule.required && (!value || (typeof value === "string" && !value.trim()))) {
        return "This field is required"
      }

      // Skip other validations if field is empty and not required
      if (!value || (typeof value === "string" && !value.trim())) {
        return null
      }

      // String-based validations
      if (typeof value === "string") {
        // Min length
        if (rule.minLength && value.length < rule.minLength) {
          return `Must be at least ${rule.minLength} characters`
        }

        // Max length
        if (rule.maxLength && value.length > rule.maxLength) {
          return `Must not exceed ${rule.maxLength} characters`
        }

        // Pattern validation
        if (rule.pattern && !rule.pattern.test(value)) {
          return "Invalid format"
        }
      }

      // Custom validation
      if (rule.custom) {
        const customError = rule.custom(value)
        if (customError) return customError
      }

      // Built-in validations based on field name
      if (field.toLowerCase().includes("email")) {
        return validateEmail(value)
      }
      if (field.toLowerCase().includes("password")) {
        return validatePassword(value)
      }
      if (field.toLowerCase().includes("username")) {
        return validateUsername(value)
      }
      if (field.toLowerCase().includes("phone")) {
        return validatePhone(value)
      }
      if (field.toLowerCase().includes("name")) {
        return validateName(value)
      }

      return null
    },
    [rules],
  )

  const validate = useCallback(
    (field?: string): boolean => {
      if (field) {
        // Validate single field
        const error = validateField(field, data[field])
        setErrors((prev) => ({
          ...prev,
          [field]: error || "",
        }))
        return !error
      }
      // Validate all fields
      const newErrors: Record<string, string> = {}
      let isValid = true

      for (const fieldName of Object.keys(rules)) {
        const error = validateField(fieldName, data[fieldName])
        if (error) {
          newErrors[fieldName] = error
          isValid = false
        }
      }

      setErrors(newErrors)
      return isValid
    },
    [data, rules, validateField],
  )

  const clearErrors = useCallback((field?: string) => {
    if (field) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    } else {
      setErrors({})
    }
  }, [])

  const isValid = Object.values(errors).every((error) => !error)

  return {
    errors,
    isValid,
    validate,
    validateField,
    clearErrors,
  }
}

export default useValidation
