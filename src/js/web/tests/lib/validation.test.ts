import { describe, expect, it } from "vitest"
import { getPasswordStrength, MAX_PASSWORD_STRENGTH_SCORE, newPasswordSchema } from "@/lib/validation"

describe("newPasswordSchema", () => {
  it("accepts any password of 12 to 128 characters, whatever it is made of", () => {
    expect(newPasswordSchema.safeParse("abcdefghijkl").success).toBe(true)
    expect(newPasswordSchema.safeParse("a".repeat(128)).success).toBe(true)
  })

  it("rejects a password shorter than 12 characters", () => {
    const result = newPasswordSchema.safeParse("abcdefghijk")

    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.message).toBe("Password must be at least 12 characters long")
  })

  it("rejects a password longer than 128 characters", () => {
    const result = newPasswordSchema.safeParse("a".repeat(129))

    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.message).toBe("Password must not exceed 128 characters")
  })
})

describe("getPasswordStrength", () => {
  it("never scores a password above the maximum the meter is scaled to", () => {
    const strongest = getPasswordStrength("Tr0ub4dor&Horse!Staple-Battery")

    expect(strongest.level).toBe("strong")
    expect(strongest.score).toBe(MAX_PASSWORD_STRENGTH_SCORE)
  })

  it("rates an acceptable single-class password as weak rather than failing it", () => {
    const allLowercase = getPasswordStrength("abcdefghijkl")

    expect(allLowercase.hasRequiredLength).toBe(true)
    expect(allLowercase.level).toBe("weak")
    expect(allLowercase.characterClasses).toEqual({ uppercase: false, lowercase: true, digits: false, symbols: false })
  })
})
