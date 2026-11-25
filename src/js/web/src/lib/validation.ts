import { z } from "zod"

const PASSWORD_MIN_LENGTH = 12
const PASSWORD_MAX_LENGTH = 128
const UPPERCASE_PATTERN = /[A-Z]/
const LOWERCASE_PATTERN = /[a-z]/
const DIGIT_PATTERN = /\d/
const SPECIAL_CHARACTER_PATTERN = /[!@#$%^&*(),.?":{}|<>_+=\-[\]\\/~`]/
const COMMON_PASSWORD_PATTERNS = [
  /password/i,
  /123456/,
  /qwerty/i,
  /admin/i,
  /(.)\1{4,}/, // one character repeated five or more times
  /^(012|123|234|345|456|567|678|789|890|abc|bcd|cde)/i, // leading digit or letter run
  /^(qwe|asd|zxc)/i, // leading keyboard row
]
const COMMON_PASSWORD_MESSAGE = "Password is too common - please choose a more unique password"

export type PasswordStrengthLevel = "weak" | "medium" | "strong"

export interface PasswordRequirements {
  length: boolean
  uppercase: boolean
  lowercase: boolean
  digits: boolean
  special: boolean
  notCommon: boolean
}

export interface PasswordStrengthReport {
  score: number
  level: PasswordStrengthLevel
  requirements: PasswordRequirements
  feedback: string[]
}

const STRENGTH_CRITERIA: ReadonlyArray<{ requirement: keyof PasswordRequirements; points: number; hint: string }> = [
  { requirement: "length", points: 2, hint: `Use at least ${PASSWORD_MIN_LENGTH} characters` },
  { requirement: "uppercase", points: 1, hint: "Include uppercase letters" },
  { requirement: "lowercase", points: 1, hint: "Include lowercase letters" },
  { requirement: "digits", points: 1, hint: "Include numbers" },
  { requirement: "special", points: 1, hint: "Include special characters (!@#$%^&*)" },
  { requirement: "notCommon", points: 1, hint: "Avoid common passwords" },
]

const LENGTH_BONUS_THRESHOLDS = [16, 20]

export const MAX_PASSWORD_STRENGTH_SCORE = STRENGTH_CRITERIA.reduce((total, { points }) => total + points, 0) + LENGTH_BONUS_THRESHOLDS.length

function isCommonPassword(password: string): boolean {
  return COMMON_PASSWORD_PATTERNS.some((pattern) => pattern.test(password))
}

function strengthLevel(score: number): PasswordStrengthLevel {
  if (score >= 7) return "strong"
  if (score >= 5) return "medium"
  return "weak"
}

/**
 * Returns the first password rule the value breaks, or null when it is empty or acceptable.
 * The rules mirror the backend password policy.
 */
export function validatePassword(password: string): string | null {
  if (!password) return null

  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters long`
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `Password must not exceed ${PASSWORD_MAX_LENGTH} characters`
  }
  if (!UPPERCASE_PATTERN.test(password)) {
    return "Password must contain at least one uppercase letter"
  }
  if (!LOWERCASE_PATTERN.test(password)) {
    return "Password must contain at least one lowercase letter"
  }
  if (!DIGIT_PATTERN.test(password)) {
    return "Password must contain at least one digit"
  }
  if (!SPECIAL_CHARACTER_PATTERN.test(password)) {
    return "Password must contain at least one special character"
  }
  if (isCommonPassword(password)) {
    return COMMON_PASSWORD_MESSAGE
  }
  return null
}

export function getPasswordStrength(password: string): PasswordStrengthReport {
  const requirements: PasswordRequirements = {
    length: password.length >= PASSWORD_MIN_LENGTH,
    uppercase: UPPERCASE_PATTERN.test(password),
    lowercase: LOWERCASE_PATTERN.test(password),
    digits: DIGIT_PATTERN.test(password),
    special: SPECIAL_CHARACTER_PATTERN.test(password),
    notCommon: !isCommonPassword(password),
  }

  let score = 0
  const feedback: string[] = []
  for (const { requirement, points, hint } of STRENGTH_CRITERIA) {
    if (requirements[requirement]) {
      score += points
    } else {
      feedback.push(hint)
    }
  }
  // Longer passwords earn a bonus point per threshold beyond the minimum length.
  score += LENGTH_BONUS_THRESHOLDS.filter((threshold) => password.length >= threshold).length

  return { score, level: strengthLevel(score), requirements, feedback }
}

export const loginFormSchema = z.object({
  username: z.string().min(1, "Email or username is required"),
  password: z.string().min(1, "Password is required").max(128, "Password must be less than 128 characters"),
})

export type LoginFormData = z.infer<typeof loginFormSchema>

/** A password a user is choosing, checked against the full password policy. */
export const newPasswordSchema = z
  .string()
  .min(1, "Password is required")
  .superRefine((password, context) => {
    const policyError = validatePassword(password)
    if (policyError) {
      context.addIssue({ code: z.ZodIssueCode.custom, message: policyError })
    }
  })
