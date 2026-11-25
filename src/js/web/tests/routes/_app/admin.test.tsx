import { screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { buildUser, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

describe("admin routes", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("redirects a non-superuser to home before any admin page loads", async () => {
    mockApi({ "GET /api/me": buildUser({ isSuperuser: false }), "GET /api/teams": { items: [], total: 0 } })

    const { router } = renderApp("/admin/users")

    expect(await screen.findByText(/Welcome back/)).toBeInTheDocument()
    expect(router.state.location.pathname).toBe("/home")
    expect(router.state.redirect).toBeUndefined()
    expect(router.state.matches.some((match) => match.routeId.startsWith("/_app/admin"))).toBe(false)
  })

  it("lets a superuser open the admin console", async () => {
    mockApi({ "GET /api/me": buildUser({ isSuperuser: true }), "GET /api/teams": { items: [], total: 0 } })

    const { router } = renderApp("/admin")

    expect(await screen.findByRole("heading", { name: "Admin Console" })).toBeInTheDocument()
    await waitFor(() => expect(router.state.location.pathname).toBe("/admin"))
  })
})
