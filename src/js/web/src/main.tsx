import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import React from "react"
import ReactDOM from "react-dom/client"
import { client } from "@/lib/generated/api/client.gen"
import { ThemeProvider } from "@/lib/theme-context"

// Import the generated route tree
import { routeTree } from "./routeTree.gen"

import "./styles.css"
import reportWebVitals from "./reportWebVitals.ts"

// Extend Window type for CSRF token injected by litestar-vite
declare global {
  interface Window {
    __LITESTAR_CSRF__?: string
  }
}

const queryClient = new QueryClient()

const apiUrl = import.meta.env.VITE_API_URL ?? ""

client.setConfig({
  baseUrl: apiUrl,
  credentials: "include",
  auth: () => {
    if (typeof window === "undefined") {
      return undefined
    }
    return window.localStorage.getItem("access_token") ?? undefined
  },
})

// Add CSRF token to all non-GET requests
// litestar-vite injects the token into window.__LITESTAR_CSRF__
client.interceptors.request.use((request, _options) => {
  const method = request.method?.toUpperCase()
  // Only add CSRF header for unsafe methods (non-GET/HEAD/OPTIONS)
  if (method && !["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrfToken = window.__LITESTAR_CSRF__
    if (csrfToken) {
      request.headers.set("X-XSRF-TOKEN", csrfToken)
    }
  }
  return request
})

// Silent token refresh state
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: Error | null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  failedQueue = []
}

// Response interceptor for silent token refresh
// Using error interceptor with the new client API
client.interceptors.error.use(async (error, response, request, options) => {
  // Only attempt refresh for 401 errors, not on refresh endpoint itself
  const requestUrl = request.url
  if (
    response?.status === 401 &&
    !requestUrl?.includes("/api/access/refresh") &&
    !requestUrl?.includes("/api/access/login")
  ) {
    if (isRefreshing) {
      // If already refreshing, queue this request
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => {
        const method = options.method ?? "GET"
        return client.request({ ...options, method, url: requestUrl })
      })
    }

    isRefreshing = true

    try {
      // Attempt to refresh the token
      await client.post({ url: "/api/access/refresh" })
      processQueue(null)
      // Retry the original request
      const method = options.method ?? "GET"
      return client.request({ ...options, method, url: requestUrl })
    } catch (refreshError) {
      processQueue(refreshError as Error)
      // Refresh failed - clear auth state and redirect to login
      queryClient.clear()
      window.location.href = "/login"
      throw refreshError
    } finally {
      isRefreshing = false
    }
  }

  throw error
})

// Create the router using the generated route tree
const router = createRouter({
  routeTree,
  context: {
    queryClient,
  },
  defaultPreload: "intent",
  scrollRestoration: true,
  defaultStructuralSharing: true,
  defaultPreloadStaleTime: 0,
})

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

// Render the app
const rootElement = document.getElementById("root")
if (rootElement && !rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <React.StrictMode>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
          <ReactQueryDevtools />
        </QueryClientProvider>
      </ThemeProvider>
    </React.StrictMode>,
  )
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals()
