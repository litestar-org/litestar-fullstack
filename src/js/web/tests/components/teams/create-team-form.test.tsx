import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { listTagsQueryKey } from "@/lib/generated/api/@tanstack/react-query.gen"
import { buildTeam, buildUser, jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("CreateTeamForm", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("suggests tags from the shared tag cache and lists the new team after creating it", async () => {
    const teams = [buildTeam({ id: "team-1", name: "Engineering" })]
    mockApi({
      "GET /api/me": buildUser(),
      "GET /api/teams": () => jsonResponse({ items: teams, total: teams.length }),
      "GET /api/tags": { items: [{ id: "tag-1", name: "platform", slug: "platform" }], total: 1 },
      "POST /api/teams": () => {
        const created = buildTeam({ id: "team-2", name: "Design", slug: "design" })
        teams.push(created)
        return jsonResponse(created, 201)
      },
    })

    const { router, queryClient } = renderApp("/teams/new")

    await userEvent.type(await screen.findByPlaceholderText("Engineering"), "Design")
    await userEvent.type(screen.getByPlaceholderText("Type a tag and press Enter..."), "plat")
    expect(await screen.findByRole("button", { name: /platform/ })).toBeInTheDocument()
    expect(queryClient.getQueryData(listTagsQueryKey())).toMatchObject({ items: [{ name: "platform" }] })

    await userEvent.click(screen.getByRole("button", { name: "Create Team" }))

    await waitFor(() => expect(router.state.location.pathname).toBe("/teams"))
    expect(await screen.findByText("Showing 2 of 2 teams")).toBeInTheDocument()
  })
})
