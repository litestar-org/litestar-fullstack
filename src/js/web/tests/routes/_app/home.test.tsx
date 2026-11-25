import { screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { buildTeam, buildUser, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("home page", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("shares one teams request with the sidebar", async () => {
    const teams = ["Engineering", "Design", "Support", "Sales"].map((name) => buildTeam({ id: name.toLowerCase(), name, slug: name.toLowerCase() }))
    const api = mockApi({ "GET /api/me": buildUser(), "GET /api/teams": { items: teams, total: teams.length } })

    renderApp("/home")

    expect(await screen.findByText("View all 4 teams")).toBeInTheDocument()
    expect(api.requestCount("GET /api/teams")).toBe(1)
  })
})
