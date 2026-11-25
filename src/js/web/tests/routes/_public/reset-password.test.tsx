import { act, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

const NEW_PASSWORD = "Tr0ub4dor&Horse!Staple"

describe("reset password page", () => {
  beforeEach(setUpApiClient)
  afterEach(() => {
    vi.useRealTimers()
    tearDownApp()
  })

  it("shows why the server rejected an acceptable-length password", async () => {
    mockApi({
      "POST /api/access/password/reset": () => jsonResponse({ status: 400, title: "Bad Request", detail: "Password matches your email." }, 400),
    })

    renderApp("/reset-password?token=reset-token")
    await userEvent.type(await screen.findByPlaceholderText("Enter new password"), "member@example.com")
    await userEvent.type(screen.getByPlaceholderText("Confirm new password"), "member@example.com")
    await userEvent.click(screen.getByRole("button", { name: "Reset password" }))

    expect(await screen.findByText("Password matches your email.")).toBeInTheDocument()
  })

  it("names both possible causes when the server rejects the reset without saying why", async () => {
    mockApi({
      "POST /api/access/password/reset": () => jsonResponse({ status: 400, title: "Bad Request", detail: "The request is invalid." }, 400),
    })

    renderApp("/reset-password?token=reset-token")
    await userEvent.type(await screen.findByPlaceholderText("Enter new password"), "passwordpass")
    await userEvent.type(screen.getByPlaceholderText("Confirm new password"), "passwordpass")
    await userEvent.click(screen.getByRole("button", { name: "Reset password" }))

    expect(
      await screen.findByText("We couldn't reset your password. The link may have expired, or the password may be too common. Request a new link or choose a different password."),
    ).toBeInTheDocument()
    expect(screen.queryByText("The request is invalid.")).not.toBeInTheDocument()
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
