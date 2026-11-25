import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { toast } from "sonner"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("forgot password page", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("shows the reason the API gives when the reset email cannot be sent", async () => {
    const toastError = vi.spyOn(toast, "error")
    mockApi({
      "POST /api/access/password/recovery": () => jsonResponse({ status: 429, detail: "Too many reset requests. Try again in a minute." }, 429),
    })

    renderApp("/forgot-password")
    await userEvent.type(await screen.findByPlaceholderText("you@example.com"), "member@example.com")
    await userEvent.click(screen.getByRole("button", { name: "Send reset email" }))

    await waitFor(() => expect(toastError).toHaveBeenCalledWith("Too many reset requests. Try again in a minute."))
  })
})
