import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { createMemoryHistory, createRouter, RouterProvider } from "@tanstack/react-router"
import { render } from "@testing-library/react"
import { StrictMode } from "react"
import { vi } from "vitest"
import { configureApiClient, resetApiClientForTest } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import type { Team, User } from "@/lib/generated/api"
import { CSRF_COOKIE_NAME } from "@/lib/generated/routes"
import { ThemeProvider } from "@/lib/theme-context"
import { routeTree } from "@/routeTree.gen"

type ApiHandler = (request: Request) => Response | Promise<Response>

/** Maps "METHOD /path" to a JSON body or to a handler that builds the response. */
export type ApiRoutes = Record<string, ApiHandler | object>

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
}

export function buildUser(overrides: Partial<User> = {}): User {
  return { id: "user-1", email: "member@example.com", name: "Member", hasPassword: true, isActive: true, isVerified: true, isSuperuser: false, ...overrides }
}

export function buildTeam(overrides: Partial<Team> = {}): Team {
  return { id: "team-1", name: "Engineering", slug: "engineering", members: [], tags: [], ...overrides }
}

/** Replaces `fetch` with a router over the given API routes; unlisted routes answer 404. */
export function mockApi(routes: ApiRoutes) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const request = input instanceof Request ? input : new Request(input, init)
    const route = `${request.method} ${new URL(request.url).pathname}`
    const handler = routes[route]
    if (handler === undefined) {
      return Promise.resolve(jsonResponse({ detail: `No handler for ${route}` }, 404))
    }
    return Promise.resolve(typeof handler === "function" ? handler(request) : jsonResponse(handler))
  })
  globalThis.fetch = fetchMock as typeof fetch
  return {
    requestCount: (route: string) =>
      fetchMock.mock.calls.filter(([input, init]) => {
        const request = input instanceof Request ? input : new Request(input, init)
        return `${request.method} ${new URL(request.url).pathname}` === route
      }).length,
  }
}

const originalFetch = globalThis.fetch

export function setUpApiClient() {
  resetApiClientForTest()
  configureApiClient({ baseUrl: "http://localhost" })
  document.cookie = `${CSRF_COOKIE_NAME}=test-csrf-token; path=/`
}

export function tearDownApp() {
  globalThis.fetch = originalFetch
  resetApiClientForTest()
  useAuthStore.getState().clearSession()
  sessionStorage.clear()
  vi.restoreAllMocks()
}

interface RenderAppOptions {
  strictMode?: boolean
}

/** Renders the real route tree at `path`, with a fresh query client and an in-memory history. */
export function renderApp(path: string, { strictMode = false }: RenderAppOptions = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const router = createRouter({
    routeTree,
    context: { queryClient },
    history: createMemoryHistory({ initialEntries: [path] }),
  })
  const view = render(
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ThemeProvider>,
    { wrapper: strictMode ? StrictMode : undefined },
  )
  return { ...view, router, queryClient }
}
