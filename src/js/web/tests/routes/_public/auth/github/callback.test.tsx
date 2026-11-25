import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { mockApi, renderApp, setUpApiClient, tearDownApp } from "../../../../support/app"

describe("GitHub callback page", () => {
  beforeEach(setUpApiClient)
  afterEach(() => {
    vi.unstubAllGlobals()
    tearDownApp()
  })

  it("restarts GitHub sign-in when the user chooses to try again", async () => {
    const assign = vi.fn()
    vi.stubGlobal("location", { ...window.location, assign })
    mockApi({})

    renderApp("/auth/github/callback?error=access_denied")
    expect(await screen.findByText("You denied access to your GitHub account")).toBeInTheDocument()
    await userEvent.click(screen.getByRole("button", { name: "Try Again" }))

    expect(assign).toHaveBeenCalledWith(`/api/auth/oauth/github/login?return_to=${encodeURIComponent("/auth/github/callback")}`)
  })
})
