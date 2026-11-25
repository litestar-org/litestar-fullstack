import { screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { useAuthStore } from "@/lib/auth"
import { buildTeam, buildUser, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("TeamList", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("marks the current team without leaking a stray class onto its avatar", async () => {
    const team = buildTeam()
    mockApi({ "GET /api/me": buildUser(), "GET /api/teams": { items: [team], total: 1 } })
    useAuthStore.setState({ currentTeam: team })

    const { container } = renderApp("/teams")

    expect(await screen.findByTitle("Current team")).toBeInTheDocument()
    expect(container.querySelector(".false")).toBeNull()
  })
})
