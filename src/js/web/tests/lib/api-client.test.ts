import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { configureApiClient, extractApiErrorMessage, isApplicationAccessRequired, isReauthenticationRequired, resetApiClientForTest } from "@/lib/api-client"
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

  it("invokes onAccessDenied once per response that says the account lacks application access", async () => {
    const accessDenied = { status: 403, title: "Forbidden", detail: "Application access is required.", code: "application_access_required" }
    const forbidden = { status: 403, title: "Forbidden", detail: "You do not have the required role.", code: "missing_role" }
    const fetchSpy = vi.fn<typeof fetch>()
    globalThis.fetch = fetchSpy
    const onAccessDenied = vi.fn()
    const onUnauthorized = vi.fn()

    configureApiClient({ baseUrl: "http://localhost:8000", onAccessDenied, onUnauthorized })
    configureApiClient({ baseUrl: "http://localhost:8000", onAccessDenied, onUnauthorized })

    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(accessDenied), { status: 403, headers: { "Content-Type": "application/json" } }))
    await client.get({ url: "/api/me" })
    expect(onAccessDenied).toHaveBeenCalledTimes(1)
    expect(onUnauthorized).not.toHaveBeenCalled()

    onAccessDenied.mockClear()
    window.history.pushState({}, "", "/login")
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(accessDenied), { status: 403, headers: { "Content-Type": "application/json" } }))
    await client.get({ url: "/api/me" })
    expect(onAccessDenied).toHaveBeenCalledTimes(1)

    onAccessDenied.mockClear()
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify(forbidden), { status: 403, headers: { "Content-Type": "application/json" } }))
    await client.get({ url: "/api/admin/users" })
    fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } }))
    await client.post({ url: "/api/access/logout" })
    expect(onAccessDenied).not.toHaveBeenCalled()
  })
})

describe("isApplicationAccessRequired", () => {
  it("recognizes only the application access denial among API errors", () => {
    expect(isApplicationAccessRequired({ status: 403, title: "Forbidden", detail: "Application access is required.", code: "application_access_required" })).toBe(true)
    expect(isApplicationAccessRequired({ status: 403, title: "Forbidden", detail: "Confirm your password to continue.", code: "reauthentication_required" })).toBe(false)
    expect(isApplicationAccessRequired({ status: 403, title: "Forbidden" })).toBe(false)
    expect(isApplicationAccessRequired(new Error("network down"))).toBe(false)
    expect(isApplicationAccessRequired(null)).toBe(false)
  })
})

describe("isReauthenticationRequired", () => {
  it("recognizes only the reauthentication denial among API errors", () => {
    expect(isReauthenticationRequired({ status: 403, title: "Forbidden", detail: "Confirm your password to continue.", code: "reauthentication_required" })).toBe(true)
    expect(isReauthenticationRequired({ status: 403, title: "Forbidden", detail: "The current password is incorrect." })).toBe(false)
    expect(isReauthenticationRequired({ status: 403, title: "Forbidden", detail: "You do not have the required role.", code: "missing_role" })).toBe(false)
    expect(isReauthenticationRequired(new Error("network down"))).toBe(false)
    expect(isReauthenticationRequired(null)).toBe(false)
  })
})

describe("extractApiErrorMessage", () => {
  it("prefers the detail, then a message, and uses the bare title only when neither is present", () => {
    expect(extractApiErrorMessage({ status: 403, title: "Forbidden", detail: "Confirm your password to continue." }, "Try again")).toBe("Confirm your password to continue.")
    expect(extractApiErrorMessage({ status: 409, title: "Conflict", message: "This invitation was already used." }, "Try again")).toBe("This invitation was already used.")
    expect(extractApiErrorMessage({ status: 403, title: "Forbidden" }, "Try again")).toBe("Forbidden")
    expect(extractApiErrorMessage({ status: 500 }, "Try again")).toBe("Try again")
  })
})
