import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { AuditLogTable } from "@/components/admin/audit-log-table"
import { mockApi, setUpApiClient, tearDownApp } from "../../support/app"

describe("AuditLogTable", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("keeps the search box focused while each keystroke reloads the results", async () => {
    mockApi({
      "GET /api/admin/audit": { items: [{ id: "log-1", action: "user.login", createdAt: "2026-11-24T12:00:00Z" }], total: 1 },
    })
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <AuditLogTable />
      </QueryClientProvider>,
    )

    const searchBox = await screen.findByPlaceholderText("Search")
    await userEvent.type(searchBox, "login")

    expect(screen.getByPlaceholderText("Search")).toHaveValue("login")
    expect(screen.getByPlaceholderText("Search")).toHaveFocus()
    expect(await screen.findByText("user.login")).toBeInTheDocument()
  })
})
