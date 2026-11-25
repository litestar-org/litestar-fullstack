import { z } from "zod"

const PASSWORD_MIN_LENGTH = 12
const PASSWORD_MAX_LENGTH = 128

export type PasswordStrengthLevel = "weak" | "medium" | "strong"

export interface PasswordCharacterClasses {
  uppercase: boolean
  lowercase: boolean
  digits: boolean
  symbols: boolean
}

/** Guidance for the strength meter. Only `hasRequiredLength` reflects a rule the server enforces. */
export interface PasswordStrengthReport {
  score: number
  level: PasswordStrengthLevel
  hasRequiredLength: boolean
  characterClasses: PasswordCharacterClasses
}

const CHARACTER_CLASS_PATTERNS: Record<keyof PasswordCharacterClasses, RegExp> = {
  uppercase: /[A-Z]/,
  lowercase: /[a-z]/,
  digits: /\d/,
  symbols: /[^A-Za-z0-9\s]/,
}

const REQUIRED_LENGTH_POINTS = 2
const LENGTH_BONUS_THRESHOLDS = [16, 20]

export const MAX_PASSWORD_STRENGTH_SCORE = REQUIRED_LENGTH_POINTS + Object.keys(CHARACTER_CLASS_PATTERNS).length + LENGTH_BONUS_THRESHOLDS.length

function strengthLevel(score: number): PasswordStrengthLevel {
  if (score >= 6) return "strong"
  if (score >= 4) return "medium"
  return "weak"
}

/**
 * Scores a password for the strength meter: points for meeting the required length, one per
 * character class present, and one per extra length threshold. The score never gates submission.
 */
export function getPasswordStrength(password: string): PasswordStrengthReport {
  const hasRequiredLength = password.length >= PASSWORD_MIN_LENGTH && password.length <= PASSWORD_MAX_LENGTH
  const characterClasses: PasswordCharacterClasses = {
    uppercase: CHARACTER_CLASS_PATTERNS.uppercase.test(password),
    lowercase: CHARACTER_CLASS_PATTERNS.lowercase.test(password),
    digits: CHARACTER_CLASS_PATTERNS.digits.test(password),
    symbols: CHARACTER_CLASS_PATTERNS.symbols.test(password),
  }

  const score =
    (hasRequiredLength ? REQUIRED_LENGTH_POINTS : 0) +
    Object.values(characterClasses).filter(Boolean).length +
    LENGTH_BONUS_THRESHOLDS.filter((threshold) => password.length >= threshold).length

  return { score, level: strengthLevel(score), hasRequiredLength, characterClasses }
}

/** An email input, trimmed and lower-cased before validation so the API receives its normalized form. */
export function emailField(invalidMessage: string) {
  return z.string().trim().toLowerCase().email(invalidMessage)
}

export const loginFormSchema = z.object({
  username: z.string().trim().toLowerCase().min(1, "Email or username is required"),
  password: z.string().min(1, "Password is required").max(128, "Password must be less than 128 characters"),
})

export type LoginFormData = z.infer<typeof loginFormSchema>

/**
 * A password a user is choosing. Length is the only rule checked here; the server also rejects
 * common passwords and passwords equal to the account's email, and its message is shown as-is.
 */
export const newPasswordSchema = z
  .string()
  .min(1, "Password is required")
  .min(PASSWORD_MIN_LENGTH, `Password must be at least ${PASSWORD_MIN_LENGTH} characters long`)
  .max(PASSWORD_MAX_LENGTH, `Password must not exceed ${PASSWORD_MAX_LENGTH} characters`)
