import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("UserLoginForm", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("submits an email typed with capitals and surrounding spaces trimmed and lower-cased", async () => {
    let submitted: { identifier?: string } = {}
    const api = mockApi({
      "POST /api/access/login": async (request) => {
        submitted = await request.json()
        return jsonResponse({ status: 401, title: "Unauthorized", detail: "Invalid email or password." }, 401)
      },
    })

    renderApp("/login")
    await userEvent.type(await screen.findByPlaceholderText("name@example.com"), "  Member@Example.COM  ")
    await userEvent.type(screen.getByPlaceholderText("Enter your password"), "correct horse battery")
    await userEvent.click(screen.getByRole("button", { name: "Sign In" }))

    await waitFor(() => expect(api.requestCount("POST /api/access/login")).toBe(1))
    expect(submitted.identifier).toBe("member@example.com")
  })
})
