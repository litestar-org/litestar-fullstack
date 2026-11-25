import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import type { ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { PasskeysSection } from "@/components/settings/passkeys-section"
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

function encodeBytes(text: string): ArrayBuffer {
  return new TextEncoder().encode(text).buffer
}

function makeFakeAttestationCredential() {
  return {
    id: "cred-new-1",
    rawId: encodeBytes("cred-new-1"),
    type: "public-key",
    authenticatorAttachment: "platform",
    getClientExtensionResults: () => ({}),
    response: {
      clientDataJSON: encodeBytes(JSON.stringify({ type: "webauthn.create", challenge: "dGVzdC1jaGFsbGVuZ2U", origin: "http://localhost" })),
      attestationObject: encodeBytes("attestation-bytes"),
      getTransports: () => ["internal"],
      getAuthenticatorData: () => encodeBytes("auth-data"),
      getPublicKey: () => encodeBytes("pub-key"),
      getPublicKeyAlgorithm: () => -7,
    },
  }
}

describe("PasskeysSection", () => {
  const originalFetch = globalThis.fetch
  const originalPublicKeyCredential = window.PublicKeyCredential
  const originalCredentials = navigator.credentials

  beforeEach(() => {
    resetApiClientForTest()
    configureApiClient({ baseUrl: "http://localhost" })
    document.cookie = `${CSRF_COOKIE_NAME}=test-csrf-token; path=/`
    useAuthStore.setState({
      user: { id: "user-1", email: "alice@example.com", hasPassword: true },
      teams: [],
      currentTeam: null,
      isAuthenticated: true,
      isLoading: false,
      mfaChallenge: null,
    })

    Object.defineProperty(window, "PublicKeyCredential", {
      value: function PublicKeyCredential() {},
      writable: true,
      configurable: true,
    })
    Object.defineProperty(navigator, "credentials", {
      value: {
        create: vi.fn(),
        get: vi.fn(),
      },
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    Object.defineProperty(window, "PublicKeyCredential", {
      value: originalPublicKeyCredential,
      writable: true,
      configurable: true,
    })
    Object.defineProperty(navigator, "credentials", {
      value: originalCredentials,
      writable: true,
      configurable: true,
    })
    resetApiClientForTest()
    vi.restoreAllMocks()
  })

  it("registers a new passkey and refreshes the credential list", async () => {
    let passkeys: Array<{ credential_id: string; display_name: string; created_at: string; last_used_at: string | null }> = []
    const createCredential = vi.fn().mockResolvedValue(makeFakeAttestationCredential())
    Object.defineProperty(navigator, "credentials", {
      value: { create: createCredential, get: vi.fn() },
      writable: true,
      configurable: true,
    })

    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init)
      const pathname = new URL(request.url).pathname

      if (pathname === "/api/config/auth") {
        return jsonResponse({ githubEnabled: false, passkeysEnabled: true, mfaEnabled: true })
      }
      if (pathname === "/api/access/passkeys" && request.method === "GET") {
        return jsonResponse(passkeys)
      }
      if (pathname === "/api/access/step-up/passkey-register" && request.method === "POST") {
        return jsonResponse({ grant: "grant-reg", action: "passkey-register", expires_at: "2099-01-01T00:00:00Z" })
      }
      if (pathname === "/api/access/passkeys/registration/options" && request.method === "POST") {
        return jsonResponse({
          binding: "bind-123",
          options: JSON.stringify({
            challenge: "dGVzdC1jaGFsbGVuZ2U",
            rp: { name: "Litestar App", id: "localhost" },
            user: { id: "dXNlci0x", name: "alice@example.com", displayName: "Alice" },
            pubKeyCredParams: [{ alg: -7, type: "public-key" }],
          }),
        })
      }
      if (pathname === "/api/access/passkeys/registration/verify" && request.method === "POST") {
        passkeys = [
          {
            credential_id: "cred-new-1",
            display_name: "MacBook Touch ID",
            created_at: "2026-11-24T12:00:00Z",
            last_used_at: null,
          },
        ]
        return jsonResponse({ registered: true, credential_id: "cred-new-1" })
      }
      return jsonResponse({ detail: "Not found" }, 404)
    })

    const user = userEvent.setup()
    render(<PasskeysSection />, { wrapper: createWrapper() })

    expect(await screen.findByText(/no passkeys registered yet/i)).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /add passkey/i }))
    await user.type(screen.getByPlaceholderText(/current password/i), "correct-horse-battery")
    await user.click(screen.getByRole("button", { name: /register passkey/i }))

    expect(await screen.findByText("MacBook Touch ID")).toBeInTheDocument()
    expect(createCredential).toHaveBeenCalledTimes(1)
  })

  it("handles NotAllowedError cancellation without clearing session or verifying", async () => {
    const abortError = new Error("User cancelled WebAuthn")
    abortError.name = "NotAllowedError"
    Object.defineProperty(navigator, "credentials", {
      value: { create: vi.fn().mockRejectedValue(abortError), get: vi.fn() },
      writable: true,
      configurable: true,
    })

    let verifyCalled = false
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init)
      const pathname = new URL(request.url).pathname

      if (pathname === "/api/config/auth") {
        return jsonResponse({ githubEnabled: false, passkeysEnabled: true, mfaEnabled: true })
      }
      if (pathname === "/api/access/passkeys") {
        return jsonResponse([])
      }
      if (pathname === "/api/access/step-up/passkey-register") {
        return jsonResponse({ grant: "grant-reg", action: "passkey-register", expires_at: "2099-01-01T00:00:00Z" })
      }
      if (pathname === "/api/access/passkeys/registration/options") {
        return jsonResponse({
          binding: "bind-cancel",
          options: JSON.stringify({
            challenge: "dGVzdC1jaGFsbGVuZ2U",
            rp: { name: "Litestar App", id: "localhost" },
            user: { id: "dXNlci0x", name: "alice@example.com", displayName: "Alice" },
            pubKeyCredParams: [{ alg: -7, type: "public-key" }],
          }),
        })
      }
      if (pathname === "/api/access/passkeys/registration/verify") {
        verifyCalled = true
        return jsonResponse({ registered: true })
      }
      return jsonResponse({ detail: "Not found" }, 404)
    })

    const user = userEvent.setup()
    render(<PasskeysSection />, { wrapper: createWrapper() })

    await user.click(await screen.findByRole("button", { name: /add passkey/i }))
    await user.type(screen.getByPlaceholderText(/current password/i), "correct-horse-battery")
    await user.click(screen.getByRole("button", { name: /register passkey/i }))

    await waitFor(() => {
      expect(verifyCalled).toBe(false)
      expect(useAuthStore.getState().isAuthenticated).toBe(true)
    })
  })

  it("removes an existing passkey after password step-up confirmation", async () => {
    let passkeys = [
      {
        credential_id: "cred-old-1",
        display_name: "YubiKey 5",
        created_at: "2026-11-20T12:00:00Z",
        last_used_at: null,
      },
    ]

    const deletedPaths: string[] = []
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init)
      const pathname = new URL(request.url).pathname

      if (pathname === "/api/config/auth") {
        return jsonResponse({ githubEnabled: false, passkeysEnabled: true, mfaEnabled: true })
      }
      if (pathname === "/api/access/passkeys" && request.method === "GET") {
        return jsonResponse(passkeys)
      }
      if (pathname === "/api/access/step-up/passkey-remove" && request.method === "POST") {
        return jsonResponse({ grant: "grant-del", action: "passkey-remove", expires_at: "2099-01-01T00:00:00Z" })
      }
      if (pathname === "/api/access/passkeys/cred-old-1/remove" && request.method === "POST") {
        deletedPaths.push(pathname)
        passkeys = []
        return jsonResponse({ removed: true })
      }
      return jsonResponse({ detail: "Not found" }, 404)
    })

    const user = userEvent.setup()
    render(<PasskeysSection />, { wrapper: createWrapper() })

    expect(await screen.findByText("YubiKey 5")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: /^remove$/i }))
    await user.type(screen.getByPlaceholderText(/current password/i), "correct-horse-battery")
    await user.click(screen.getByRole("button", { name: /remove passkey/i }))

    await waitFor(() => {
      expect(deletedPaths).toEqual(["/api/access/passkeys/cred-old-1/remove"])
      expect(screen.queryByText("YubiKey 5")).not.toBeInTheDocument()
    })
  })

  it("renders unsupported browser message when WebAuthn is unavailable", async () => {
    Object.defineProperty(window, "PublicKeyCredential", {
      value: undefined,
      writable: true,
      configurable: true,
    })

    globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init)
      const pathname = new URL(request.url).pathname
      if (pathname === "/api/config/auth") {
        return jsonResponse({ githubEnabled: false, passkeysEnabled: true, mfaEnabled: true })
      }
      if (pathname === "/api/access/passkeys") {
        return jsonResponse([])
      }
      return jsonResponse({ detail: "Not found" }, 404)
    })

    render(<PasskeysSection />, { wrapper: createWrapper() })

    expect(await screen.findByText(/does not support webauthn passkeys/i)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /add passkey/i })).not.toBeInTheDocument()
  })
})
