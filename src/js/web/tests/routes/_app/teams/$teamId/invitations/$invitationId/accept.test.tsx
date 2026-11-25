import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { toast } from "sonner"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { getTeamQueryKey } from "@/lib/generated/api/@tanstack/react-query.gen"
import { buildTeam, buildUser, jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../../../../../support/app"

const INVITATION_PATH = "/teams/team-1/invitations/invitation-1/accept"

describe("invitation acceptance page", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("still offers the invitation when the invitee may not look up the team", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {})
    mockApi({
      "GET /api/me": buildUser(),
      "GET /api/teams": { items: [], total: 0 },
      "GET /api/teams/team-1": () => jsonResponse({ status: 403, detail: "Not a member of this team." }, 403),
    })

    renderApp(INVITATION_PATH)

    expect(await screen.findByText("You've been invited to join a team")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Accept Invitation" })).toBeEnabled()
    expect(consoleError).not.toHaveBeenCalled()
  })

  it("stores the team under the shared team cache entry", async () => {
    mockApi({ "GET /api/me": buildUser(), "GET /api/teams": { items: [], total: 0 }, "GET /api/teams/team-1": buildTeam() })

    const { queryClient } = renderApp(INVITATION_PATH)

    expect(await screen.findByText("Engineering")).toBeInTheDocument()
    expect(queryClient.getQueryData(getTeamQueryKey({ path: { team_id: "team-1" } }))).toMatchObject({ name: "Engineering" })
  })

  it("shows the reason the API gives when accepting fails", async () => {
    const toastError = vi.spyOn(toast, "error")
    mockApi({
      "GET /api/me": buildUser(),
      "GET /api/teams": { items: [], total: 0 },
      "GET /api/teams/team-1": buildTeam(),
      "POST /api/teams/team-1/invitations/invitation-1/accept": () => jsonResponse({ status: 409, title: "Conflict", message: "This invitation was already used." }, 409),
    })

    renderApp(INVITATION_PATH)
    await userEvent.click(await screen.findByRole("button", { name: "Accept Invitation" }))

    expect(await screen.findByRole("alert")).toHaveTextContent("This invitation was already used.")
    await waitFor(() => expect(toastError).toHaveBeenCalledWith("Failed to accept invitation", { description: "This invitation was already used." }))
  })
})
