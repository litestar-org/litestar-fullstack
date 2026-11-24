import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { configureApiClient, resetApiClientForTest } from "@/lib/api-client"
import { client } from "@/lib/generated/api/client.gen"
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from "@/lib/generated/routes"

describe("configureApiClient", () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    resetApiClientForTest()
    localStorage.clear()
    document.cookie = `${CSRF_COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
    delete window.__LITESTAR_CSRF__
    window.history.pushState({}, "", "/home")
  })

  afterEach(() => {
    resetApiClientForTest()
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("sends credentials: include and omits Authorization header even with stale localStorage token", async () => {
    localStorage.setItem("access_token", "stale-jwt-token")
    const fetchSpy = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } }))
    globalThis.fetch = fetchSpy

    configureApiClient({ baseUrl: "http://localhost:8000" })
    await client.get({ url: "/api/me" })

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const req = fetchSpy.mock.calls[0]?.[0] as Request
    expect(req.credentials).toBe("include")
    expect(req.headers.get("Authorization")).toBeNull()
    expect(req.headers.get(CSRF_HEADER_NAME)).toBeNull()
  })

  it("attaches CSRF header on unsafe methods from window.__LITESTAR_CSRF__ and cookie fallback", async () => {
    const fetchSpy = vi
      .fn<typeof fetch>()
      .mockImplementation(async () => new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } }))
    globalThis.fetch = fetchSpy

    configureApiClient({ baseUrl: "http://localhost:8000" })

    window.__LITESTAR_CSRF__ = "global-csrf-token"
    await client.post({ url: "/api/tags", body: { name: "test" } })
    const postReq = fetchSpy.mock.calls[0]?.[0] as Request
    expect(postReq.headers.get(CSRF_HEADER_NAME)).toBe("global-csrf-token")

    delete window.__LITESTAR_CSRF__
    document.cookie = `${CSRF_COOKIE_NAME}=cookie-csrf-token; path=/`
    await client.delete({ url: "/api/tags/123" })
    const deleteReq = fetchSpy.mock.calls[1]?.[0] as Request
    expect(deleteReq.headers.get(CSRF_HEADER_NAME)).toBe("cookie-csrf-token")
  })

  it("invokes onUnauthorized once on 401 outside public auth routes and never calls /api/access/refresh", async () => {
    const fetchSpy = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response(JSON.stringify({ detail: "Unauthorized" }), { status: 401, headers: { "Content-Type": "application/json" } }))
    globalThis.fetch = fetchSpy
    const onUnauthorized = vi.fn()

    configureApiClient({ baseUrl: "http://localhost:8000", onUnauthorized })
    configureApiClient({ baseUrl: "http://localhost:8000", onUnauthorized })

    await client.get({ url: "/api/me" })
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
    expect(fetchSpy).toHaveBeenCalledTimes(1)

    onUnauthorized.mockClear()
    window.history.pushState({}, "", "/login")
    await client.get({ url: "/api/me" })
    expect(onUnauthorized).not.toHaveBeenCalled()

    onUnauthorized.mockClear()
    window.history.pushState({}, "", "/settings/security")
    await client.post({ url: "/api/access/step-up/totp-enroll", body: { method: "password", credential: "wrong" } })
    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
