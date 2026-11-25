import { screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { ACCESS_DENIED_LOGIN_URL } from "@/lib/redirect-utils"
import { mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("AuthForm", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("tells a user who was signed out for lacking access why they are back at login", async () => {
    mockApi({})

    renderApp(ACCESS_DENIED_LOGIN_URL)

    expect(await screen.findByText("Your account does not have access to this application.")).toBeInTheDocument()
  })

  it("shows no access notice on an ordinary visit to login", async () => {
    mockApi({})

    renderApp("/login")

    expect(await screen.findByRole("button", { name: "Sign In" })).toBeInTheDocument()
    expect(screen.queryByText("Your account does not have access to this application.")).not.toBeInTheDocument()
  })
})
