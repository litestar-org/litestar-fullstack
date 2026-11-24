import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import type { ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { MfaDisableDialog } from "@/components/mfa/mfa-disable-dialog"
import { configureApiClient, resetApiClientForTest } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"

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

describe("MfaDisableDialog", () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    resetApiClientForTest()
    configureApiClient({ baseUrl: "http://localhost" })
    document.cookie = "csrftoken=test-csrf-token; path=/"
    useAuthStore.setState({
      user: null,
      teams: [],
      currentTeam: null,
      isAuthenticated: true,
      isLoading: false,
      mfaChallenge: null,
    })
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    resetApiClientForTest()
    vi.restoreAllMocks()
  })

  describe("when user has a password", () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: "user-1",
          email: "test@example.com",
          hasPassword: true,
          isTwoFactorEnabled: true,
          oauthAccounts: [],
        },
      })
    })

    it("renders password input when dialog is opened", async () => {
      const user = userEvent.setup()
      render(<MfaDisableDialog />, { wrapper: createWrapper() })

      await user.click(screen.getByRole("button", { name: /disable mfa/i }))

      expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument()
      expect(screen.queryByRole("button", { name: /verify with/i })).not.toBeInTheDocument()
    })

    it("requests a step-up grant and disables TOTP via the API", async () => {
      const requests: Array<{ url: string; method: string; body: string | null }> = []
      globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const request = input instanceof Request ? input : new Request(input, init)
        const body = request.method === "GET" ? null : await request.clone().text()
        requests.push({ url: request.url, method: request.method, body })

        if (request.url.endsWith("/api/access/step-up/mfa-remove")) {
          return jsonResponse({
            grant: "step-up-grant-123",
            action: "mfa-remove",
            expires_at: "2099-01-01T00:00:00Z",
          })
        }
        if (request.url.endsWith("/api/access/mfa/totp/totp/remove")) {
          return jsonResponse({ removed: true })
        }
        if (request.url.endsWith("/api/me")) {
          return jsonResponse({
            id: "user-1",
            email: "test@example.com",
            hasPassword: true,
            isTwoFactorEnabled: false,
            oauthAccounts: [],
          })
        }
        return jsonResponse({ detail: "Not found" }, 404)
      })

      const user = userEvent.setup()
      render(<MfaDisableDialog />, { wrapper: createWrapper() })

      await user.click(screen.getByRole("button", { name: /disable mfa/i }))
      await user.type(screen.getByPlaceholderText(/password/i), "testpassword123")
      await user.click(screen.getByRole("button", { name: /^disable mfa$/i }))

      await waitFor(() => {
        expect(requests.map((r) => `${r.method} ${new URL(r.url).pathname}`)).toEqual([
          "POST /api/access/step-up/mfa-remove",
          "POST /api/access/mfa/totp/totp/remove",
          "GET /api/me",
        ])
      })

      expect(JSON.parse(requests[0].body ?? "{}")).toEqual({
        method: "password",
        credential: "testpassword123",
      })
      expect(JSON.parse(requests[1].body ?? "{}")).toEqual({
        step_up_grant: "step-up-grant-123",
      })
      expect(useAuthStore.getState().user?.isTwoFactorEnabled).toBe(false)
    })
  })

  describe("when user does not have a password (OAuth-only)", () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: "user-1",
          email: "test@example.com",
          hasPassword: false,
          isTwoFactorEnabled: true,
          oauthAccounts: [{ id: "oauth-1", oauthName: "github", accountId: "gh-123", accountEmail: "test@github.com" }],
        },
      })
    })

    it("renders OAuth re-authentication button instead of password input", async () => {
      const user = userEvent.setup()
      render(<MfaDisableDialog />, { wrapper: createWrapper() })

      await user.click(screen.getByRole("button", { name: /disable mfa/i }))

      expect(screen.queryByPlaceholderText(/password/i)).not.toBeInTheDocument()
      expect(screen.getByText(/re-authenticate/i)).toBeInTheDocument()
      expect(screen.getByRole("button", { name: /verify with github/i })).toBeInTheDocument()
    })

    it("redirects to the OAuth login flow when verify button is clicked", async () => {
      const user = userEvent.setup()
      const assignSpy = vi.fn()
      const originalLocation = window.location
      Object.defineProperty(window, "location", {
        value: { ...originalLocation, assign: assignSpy },
        writable: true,
        configurable: true,
      })

      try {
        render(<MfaDisableDialog />, { wrapper: createWrapper() })

        await user.click(screen.getByRole("button", { name: /disable mfa/i }))
        await user.click(screen.getByRole("button", { name: /verify with github/i }))

        expect(assignSpy).toHaveBeenCalledWith("/api/auth/oauth/github/login?return_to=%2Fsettings%2Fsecurity")
      } finally {
        Object.defineProperty(window, "location", {
          value: originalLocation,
          writable: true,
          configurable: true,
        })
      }
    })
  })

  describe("when user has multiple OAuth providers", () => {
    beforeEach(() => {
      useAuthStore.setState({
        user: {
          id: "user-1",
          email: "test@example.com",
          hasPassword: false,
          isTwoFactorEnabled: true,
          oauthAccounts: [
            { id: "oauth-1", oauthName: "github", accountId: "gh-123", accountEmail: "test@github.com" },
            { id: "oauth-2", oauthName: "google", accountId: "g-456", accountEmail: "test@gmail.com" },
          ],
        },
      })
    })

    it("shows the first OAuth provider as the verification option", async () => {
      const user = userEvent.setup()
      render(<MfaDisableDialog />, { wrapper: createWrapper() })

      await user.click(screen.getByRole("button", { name: /disable mfa/i }))

      expect(screen.getByRole("button", { name: /verify with github/i })).toBeInTheDocument()
    })
  })
})
