/**
 * Frontend validation schemas for forms using Zod.
 *
 * These are manually crafted validation schemas that provide better
 * validation rules than auto-generated schemas. They include:
 * - Proper password strength requirements
 * - Email format validation
 * - TOTP code validation (6 digits)
 * - Recovery/backup code validation (8 hex chars)
 * - Username character restrictions
 */

import { z } from "zod"

// =============================================================================
// Base Field Validators
// =============================================================================

/**
 * Email schema with format validation.
 */
export const emailSchema = z.string().min(1, "Email is required").email("Please enter a valid email address").max(255, "Email must be less than 255 characters")

/**
 * Password schema with strength requirements.
 * Requirements:
 * - At least 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 */
export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128, "Password must be less than 128 characters")
  .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
  .regex(/[a-z]/, "Password must contain at least one lowercase letter")
  .regex(/[0-9]/, "Password must contain at least one number")

/**
 * Simple password schema for login (no strength requirements).
 */
export const passwordLoginSchema = z.string().min(1, "Password is required").max(128, "Password must be less than 128 characters")

/**
 * Username schema with character restrictions.
 * Allowed: letters, numbers, underscores, hyphens.
 */
export const usernameSchema = z
  .string()
  .min(3, "Username must be at least 3 characters")
  .max(30, "Username must be less than 30 characters")
  .regex(/^[a-zA-Z0-9_-]+$/, "Username can only contain letters, numbers, underscores, and hyphens")
  .optional()

/**
 * Name schema for display names.
 */
export const nameSchema = z.string().min(1, "Name is required").max(100, "Name must be less than 100 characters").optional()

/**
 * TOTP code schema - exactly 6 digits.
 */
export const totpCodeSchema = z
  .string()
  .length(6, "Code must be exactly 6 digits")
  .regex(/^\d{6}$/, "Code must contain only numbers")

/**
 * Recovery/backup code schema - 8 alphanumeric characters.
 */
export const recoveryCodeSchema = z
  .string()
  .min(8, "Recovery code must be at least 8 characters")
  .max(16, "Recovery code must be at most 16 characters")
  .regex(/^[a-zA-Z0-9]+$/, "Recovery code must be alphanumeric")

// =============================================================================
// Form Schemas
// =============================================================================

/**
 * Login form schema.
 */
export const loginFormSchema = z.object({
  username: z.string().min(1, "Email or username is required"),
  password: passwordLoginSchema,
})

export type LoginFormData = z.infer<typeof loginFormSchema>

/**
 * Registration form schema with password confirmation.
 */
export const registerFormSchema = z
  .object({
    email: emailSchema,
    password: passwordSchema,
    passwordConfirm: z.string().min(1, "Please confirm your password"),
    name: nameSchema,
    username: usernameSchema,
    initialTeamName: z.string().max(50, "Team name must be less than 50 characters").optional(),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords do not match",
    path: ["passwordConfirm"],
  })

export type RegisterFormData = z.infer<typeof registerFormSchema>

/**
 * Forgot password form schema.
 */
export const forgotPasswordFormSchema = z.object({
  email: emailSchema,
})

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordFormSchema>

/**
 * Reset password form schema with password confirmation.
 */
export const resetPasswordFormSchema = z
  .object({
    password: passwordSchema,
    passwordConfirm: z.string().min(1, "Please confirm your password"),
    token: z.string().min(1, "Reset token is required"),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords do not match",
    path: ["passwordConfirm"],
  })

export type ResetPasswordFormData = z.infer<typeof resetPasswordFormSchema>

/**
 * MFA setup/confirm form schema.
 */
export const mfaSetupFormSchema = z.object({
  code: totpCodeSchema,
})

export type MfaSetupFormData = z.infer<typeof mfaSetupFormSchema>

/**
 * MFA disable form schema - requires password.
 */
export const mfaDisableFormSchema = z.object({
  password: passwordLoginSchema,
})

export type MfaDisableFormData = z.infer<typeof mfaDisableFormSchema>

/**
 * MFA challenge form schema - accepts either TOTP code or recovery code.
 */
export const mfaChallengeFormSchema = z
  .object({
    code: z.string().min(1, "Code is required"),
    useRecoveryCode: z.boolean().default(false),
  })
  .refine(
    (data) => {
      if (data.useRecoveryCode) {
        return recoveryCodeSchema.safeParse(data.code).success
      }
      return totpCodeSchema.safeParse(data.code).success
    },
    {
      message: "Invalid code format",
      path: ["code"],
    },
  )

export type MfaChallengeFormData = z.infer<typeof mfaChallengeFormSchema>

/**
 * Change password form schema (for authenticated users).
 */
export const changePasswordFormSchema = z
  .object({
    currentPassword: passwordLoginSchema,
    newPassword: passwordSchema,
    newPasswordConfirm: z.string().min(1, "Please confirm your new password"),
  })
  .refine((data) => data.newPassword === data.newPasswordConfirm, {
    message: "Passwords do not match",
    path: ["newPasswordConfirm"],
  })
  .refine((data) => data.currentPassword !== data.newPassword, {
    message: "New password must be different from current password",
    path: ["newPassword"],
  })

export type ChangePasswordFormData = z.infer<typeof changePasswordFormSchema>

/**
 * Profile update form schema.
 */
export const profileUpdateFormSchema = z.object({
  name: nameSchema,
  username: usernameSchema,
})

export type ProfileUpdateFormData = z.infer<typeof profileUpdateFormSchema>

/**
 * Team create/update form schema.
 */
export const teamFormSchema = z.object({
  name: z.string().min(2, "Team name must be at least 2 characters").max(50, "Team name must be less than 50 characters"),
  description: z.string().max(500, "Description must be less than 500 characters").optional(),
})

export type TeamFormData = z.infer<typeof teamFormSchema>

// =============================================================================
// Validation Helpers
// =============================================================================

/**
 * Check if a password meets strength requirements.
 * Returns an object with details about which requirements are met.
 */
export function checkPasswordStrength(password: string): {
  isValid: boolean
  minLength: boolean
  hasUppercase: boolean
  hasLowercase: boolean
  hasNumber: boolean
} {
  return {
    isValid: password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /[0-9]/.test(password),
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
  }
}

/**
 * Validate a TOTP code format (6 digits).
 */
export function isValidTotpCode(code: string): boolean {
  return /^\d{6}$/.test(code)
}

/**
 * Validate a recovery code format (alphanumeric, 8-16 chars).
 */
export function isValidRecoveryCode(code: string): boolean {
  return /^[a-zA-Z0-9]{8,16}$/.test(code)
}

/**
 * Format a recovery code for display (add dashes for readability).
 * Example: "ABCD1234" -> "ABCD-1234"
 */
export function formatRecoveryCode(code: string): string {
  const cleaned = code.replace(/[^a-zA-Z0-9]/g, "").toUpperCase()
  if (cleaned.length <= 4) return cleaned
  return `${cleaned.slice(0, 4)}-${cleaned.slice(4)}`
}
