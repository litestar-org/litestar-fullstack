import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import type { ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { ApiKeysSection } from "@/components/settings/api-keys-section"
import { configureApiClient, resetApiClientForTest } from "@/lib/api-client"
import type { ApiKeyItem } from "@/lib/generated/api"

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("ApiKeysSection", () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    resetApiClientForTest()
    configureApiClient({ baseUrl: "http://localhost" })
    document.cookie = "csrftoken=test-csrf-token; path=/"
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    resetApiClientForTest()
    vi.restoreAllMocks()
  })

  it("creates an API key, reveals the secret once, and clears it from the DOM on close", async () => {
    let keys: ApiKeyItem[] = []
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init)
      const pathname = new URL(request.url).pathname

      if (pathname === "/api/me/api-keys" && request.method === "GET") {
        return jsonResponse(keys)
      }
      if (pathname === "/api/me/api-keys" && request.method === "POST") {
        const created = {
          id: "key-1",
          name: "MCP Desktop",
          prefix: "lsk_abc1",
          scopes: ["read", "mcp"],
          createdAt: "2026-11-24T12:00:00Z",
          expiresAt: "2027-02-22T12:00:00Z",
          secret: "lsk_abc1_super_secret_plaintext_value",
        }
        keys = [
          {
            id: created.id,
            name: created.name,
            prefix: created.prefix,
            scopes: created.scopes,
            createdAt: created.createdAt,
            expiresAt: created.expiresAt,
            lastUsedAt: null,
            revokedAt: null,
          },
        ]
        return jsonResponse(created, 201)
      }
      return jsonResponse({ detail: "Not found" }, 404)
    })

    const user = userEvent.setup()
    render(<ApiKeysSection />, { wrapper: createWrapper() })

    expect(await screen.findByText(/no api keys created yet/i)).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /create api key/i }))
    await user.type(screen.getByPlaceholderText(/key name/i), "MCP Desktop")
    await user.click(screen.getByRole("button", { name: /^create key$/i }))

    expect(await screen.findByText("lsk_abc1_super_secret_plaintext_value")).toBeInTheDocument()
    expect(screen.getAllByText("MCP Desktop").length).toBeGreaterThanOrEqual(1)

    await user.click(screen.getByRole("button", { name: /i have saved this secret/i }))

    await waitFor(() => {
      expect(screen.queryByText("lsk_abc1_super_secret_plaintext_value")).not.toBeInTheDocument()
    })
  })

  it("rotates and revokes API keys through the generated endpoints", async () => {
    let keys: ApiKeyItem[] = [
      {
        id: "key-1",
        name: "CI Runner",
        prefix: "lsk_old1",
        scopes: ["read"],
        createdAt: "2026-11-20T12:00:00Z",
        expiresAt: null,
        lastUsedAt: null,
        revokedAt: null,
      },
    ]

    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init)
      const pathname = new URL(request.url).pathname

      if (pathname === "/api/me/api-keys" && request.method === "GET") {
        return jsonResponse(keys)
      }
      if (pathname === "/api/me/api-keys/key-1/rotate" && request.method === "POST") {
        keys = [
          {
            id: "key-2",
            name: "CI Runner",
            prefix: "lsk_new2",
            scopes: ["read"],
            createdAt: "2026-11-24T12:00:00Z",
            expiresAt: null,
            lastUsedAt: null,
            revokedAt: null,
          },
        ]
        return jsonResponse({
          id: "key-2",
          name: "CI Runner",
          prefix: "lsk_new2",
          scopes: ["read"],
          createdAt: "2026-11-24T12:00:00Z",
          expiresAt: null,
          secret: "lsk_new2_rotated_secret",
        })
      }
      if (pathname === "/api/me/api-keys/key-2" && request.method === "DELETE") {
        keys = []
        return new Response(null, { status: 204 })
      }
      return jsonResponse({ detail: "Not found" }, 404)
    })

    const user = userEvent.setup()
    render(<ApiKeysSection />, { wrapper: createWrapper() })

    expect(await screen.findByText("lsk_old1...")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /rotate/i }))
    expect(await screen.findByText("lsk_new2_rotated_secret")).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: /i have saved this secret/i }))

    await waitFor(() => {
      expect(screen.queryByText("lsk_new2_rotated_secret")).not.toBeInTheDocument()
      expect(screen.getByText("lsk_new2...")).toBeInTheDocument()
    })

    await user.click(screen.getByRole("button", { name: /revoke/i }))
    await waitFor(() => {
      expect(screen.queryByText("CI Runner")).not.toBeInTheDocument()
    })
  })
})
