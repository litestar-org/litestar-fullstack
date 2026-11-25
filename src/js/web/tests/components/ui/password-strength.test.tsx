import { render, waitFor } from "@testing-library/react"
import { MotionGlobalConfig } from "framer-motion"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { PasswordStrength } from "@/components/ui/password-strength"

describe("PasswordStrength", () => {
  beforeEach(() => {
    MotionGlobalConfig.skipAnimations = true
  })
  afterEach(() => {
    MotionGlobalConfig.skipAnimations = false
  })

  it("fills the meter exactly for the strongest password", async () => {
    const { container } = render(<PasswordStrength password="Tr0ub4dor&Horse!Staple-Battery" />)

    const meterFill = container.querySelector<HTMLElement>(".bg-success")
    await waitFor(() => expect(meterFill).toHaveStyle({ width: "100%" }))
  })
})
