import { screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { buildUser, jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("verify email page", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("submits the single-use token once, even when effects run twice", async () => {
    let isTokenUsed = false
    const api = mockApi({
      "GET /api/me": buildUser(),
      "POST /api/access/verification/confirm": () => {
        if (isTokenUsed) {
          return jsonResponse({ status: 400, detail: "Verification token has already been used." }, 400)
        }
        isTokenUsed = true
        return jsonResponse({ verified: true })
      },
    })

    renderApp("/verify-email?token=single-use-token", { strictMode: true })

    expect(await screen.findByText("Email Verified!")).toBeInTheDocument()
    expect(api.requestCount("POST /api/access/verification/confirm")).toBe(1)
  })
})
