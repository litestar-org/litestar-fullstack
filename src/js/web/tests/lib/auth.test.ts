import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { configureApiClient, resetApiClientForTest } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"

vi.mock("@simplewebauthn/browser", () => ({
  browserSupportsWebAuthn: () => true,
  startAuthentication: vi.fn(async () => ({ id: "cred-1", rawId: "cred-1", type: "public-key", response: {} })),
}))

describe("useAuthStore", () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    resetApiClientForTest()
    localStorage.clear()
    useAuthStore.getState().clearSession()
    configureApiClient({ baseUrl: "http://localhost:8000" })
  })

  afterEach(() => {
    resetApiClientForTest()
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("authenticates via session cookie login without writing localStorage access_token", async () => {
    const fetchSpy = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "u-1", email: "user@example.com" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "u-1",
            email: "user@example.com",
            name: "Test User",
            isActive: true,
            isSuperuser: false,
            isVerified: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
    globalThis.fetch = fetchSpy

    const result = await useAuthStore.getState().login("user@example.com", "StrongPassword!123")
    expect(result).toEqual({ authenticated: true, mfaRequired: false })
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().user?.email).toBe("user@example.com")
    expect(localStorage.getItem("access_token")).toBeNull()
  })

  it("returns mfaRequired and stores pending challenge on 403 MFA challenge response", async () => {
    globalThis.fetch = vi.fn<typeof fetch>().mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          challenge: "opaque-challenge",
          account_id: "u-mfa",
          code: "mfa_required",
          methods: ["totp", "recovery-code"],
          totp_method_ids: ["totp-1"],
        }),
        { status: 403, headers: { "Content-Type": "application/json" } },
      ),
    )

    const result = await useAuthStore.getState().login("mfa@example.com", "StrongPassword!123")
    expect(result.authenticated).toBe(false)
    expect(result.mfaRequired).toBe(true)
    expect(result.challengeToken).toBe("opaque-challenge")
    expect(useAuthStore.getState().mfaChallenge?.accountId).toBe("u-mfa")
    expect(useAuthStore.getState().mfaChallenge?.totpMethodIds).toEqual(["totp-1"])
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it("authenticates via usernameless discoverable passkey without prior account_id", async () => {
    const fetchSpy = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            options: JSON.stringify({ challenge: "c-1", rpId: "localhost" }),
            expires_at: "2026-11-25T02:00:00Z",
            binding: "bind-1",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "u-pk", email: "pk@example.com" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "u-pk", email: "pk@example.com", name: "Passkey User" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    globalThis.fetch = fetchSpy

    const ok = await useAuthStore.getState().loginWithPasskey()
    expect(ok).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().user?.email).toBe("pk@example.com")
    expect(fetchSpy).toHaveBeenCalledTimes(3)
  })

  it("checkAuth returns true on 200, false on 401, and throws on 503", async () => {
    globalThis.fetch = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "u-1", email: "ok@example.com" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Database unavailable" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        }),
      )

    expect(await useAuthStore.getState().checkAuth()).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    expect(await useAuthStore.getState().checkAuth()).toBe(false)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)

    await expect(useAuthStore.getState().checkAuth()).rejects.toThrow(/Database unavailable/)
  })

  it("logout calls backend session logout and clears store state", async () => {
    useAuthStore.setState({
      user: { id: "u-1", email: "user@example.com" },
      isAuthenticated: true,
    })
    const fetchSpy = vi.fn<typeof fetch>().mockResolvedValueOnce(new Response(null, { status: 204 }))
    globalThis.fetch = fetchSpy

    await useAuthStore.getState().logout()
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })
})
