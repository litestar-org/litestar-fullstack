import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import type { ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { MfaDisableDialog } from "@/components/mfa/mfa-disable-dialog"
import { configureApiClient, resetApiClientForTest } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import { CSRF_COOKIE_NAME } from "@/lib/generated/routes"

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
    document.cookie = `${CSRF_COOKIE_NAME}=test-csrf-token; path=/`
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
          totpMethodId: "totp-factor-1",
          oauthAccounts: [],
        },
      })
    })

    it("renders password input when dialog is opened", async () => {
      const user = userEvent.setup()
      render(<MfaDisableDialog />, { wrapper: createWrapper() })

      await user.click(screen.getByRole("button", { name: /disable mfa/i }))

      expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument()
    })

    it("requests a totp-remove step-up grant and disables the enrolled TOTP factor via the API", async () => {
      const requests: Array<{ url: string; method: string; body: string | null }> = []
      globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const request = input instanceof Request ? input : new Request(input, init)
        const body = request.method === "GET" ? null : await request.clone().text()
        requests.push({ url: request.url, method: request.method, body })

        if (request.url.endsWith("/api/access/step-up/totp-remove")) {
          return jsonResponse({
            grant: "step-up-grant-123",
            purpose: "totp-remove",
            expires_at: "2099-01-01T00:00:00Z",
          })
        }
        if (request.url.endsWith("/api/access/mfa/totp/totp-factor-1/remove")) {
          return jsonResponse({ detail: "Login method removed." })
        }
        if (request.url.endsWith("/api/me")) {
          return jsonResponse({
            id: "user-1",
            email: "test@example.com",
            hasPassword: true,
            isTwoFactorEnabled: false,
            totpMethodId: null,
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
          "POST /api/access/step-up/totp-remove",
          "POST /api/access/mfa/totp/totp-factor-1/remove",
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
          totpMethodId: "totp-factor-1",
          oauthAccounts: [{ id: "oauth-1", oauthName: "github", accountId: "gh-123", accountEmail: "test@github.com" }],
        },
      })
    })

    it("explains that password step-up verification is required before disabling MFA", async () => {
      const user = userEvent.setup()
      render(<MfaDisableDialog />, { wrapper: createWrapper() })

      await user.click(screen.getByRole("button", { name: /disable mfa/i }))

      expect(screen.queryByPlaceholderText(/password/i)).not.toBeInTheDocument()
      expect(screen.getByText(/set a password in your profile settings/i)).toBeInTheDocument()
    })
  })
})
