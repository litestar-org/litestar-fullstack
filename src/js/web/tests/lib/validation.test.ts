import { describe, expect, it } from "vitest"
import { getPasswordStrength, MAX_PASSWORD_STRENGTH_SCORE } from "@/lib/validation"

describe("getPasswordStrength", () => {
  it("never scores a password above the maximum the meter is scaled to", () => {
    const strongest = getPasswordStrength("Tr0ub4dor&Horse!Staple-Battery")

    expect(strongest.feedback).toEqual([])
    expect(strongest.score).toBe(MAX_PASSWORD_STRENGTH_SCORE)
  })
})
