import { act, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { useAuthStore } from "@/lib/auth"
import { buildTeam, buildUser, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../../../support/app"

describe("team detail page", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("does not treat a signed-out viewer as the owner of an ownerless team", async () => {
    const team = buildTeam({ members: [{ id: "member-1", userId: "user-2", name: "Other Member", email: "other@example.com", role: "MEMBER", isOwner: false }] })
    mockApi({
      "GET /api/me": buildUser(),
      "GET /api/teams": { items: [team], total: 1 },
      "GET /api/teams/team-1": team,
      "GET /api/teams/team-1/invitations": { items: [], total: 0 },
    })

    renderApp("/teams/team-1")
    expect(await screen.findByText("Other Member")).toBeInTheDocument()
    act(() => useAuthStore.setState({ user: null }))

    expect(screen.queryByRole("button", { name: "Invite" })).not.toBeInTheDocument()
  })
})
