import { act, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

const NEW_PASSWORD = "Tr0ub4dor&Horse!Staple"

describe("reset password page", () => {
  beforeEach(setUpApiClient)
  afterEach(() => {
    vi.useRealTimers()
    tearDownApp()
  })

  it("does not pull the user back to login after they have already left the page", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    mockApi({ "POST /api/access/password/reset": { reset: true } })

    const { router } = renderApp("/reset-password?token=reset-token")
    await user.type(await screen.findByPlaceholderText("Enter new password"), NEW_PASSWORD)
    await user.type(screen.getByPlaceholderText("Confirm new password"), NEW_PASSWORD)
    await user.click(screen.getByRole("button", { name: "Reset password" }))
    expect(await screen.findByText("Password Reset Successfully")).toBeInTheDocument()

    await act(() => router.navigate({ to: "/forgot-password" }))
    await waitFor(() => expect(router.state.location.pathname).toBe("/forgot-password"))
    await act(() => vi.advanceTimersByTimeAsync(5000))

    expect(router.state.location.pathname).toBe("/forgot-password")
  })
})
