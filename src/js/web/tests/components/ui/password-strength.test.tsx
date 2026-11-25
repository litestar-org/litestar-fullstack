import { render, screen, waitFor } from "@testing-library/react"
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

  it("still renders the meter for an acceptable all-lowercase password, without calling character classes required", () => {
    const { container } = render(<PasswordStrength password="abcdefghijkl" />)

    expect(screen.getByText("Password strength")).toBeInTheDocument()
    expect(screen.getByText("weak")).toBeInTheDocument()
    expect(screen.getByText("12 to 128 characters")).toBeInTheDocument()
    expect(screen.getByText("Uppercase letters")).toBeInTheDocument()
    expect(container).not.toHaveTextContent(/requirements|must contain|\bone (uppercase|lowercase|number|special)|\binclude\b/i)
  })
})
