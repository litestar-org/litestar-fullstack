import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import React from "react"
import ReactDOM from "react-dom/client"
import { ErrorBoundary } from "@/components/error-boundary"
import { configureApiClient } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import { ACCESS_DENIED_LOGIN_URL, buildRedirectUrl } from "@/lib/redirect-utils"
import { ThemeProvider } from "@/lib/theme-context"
import { routeTree } from "./routeTree.gen"

import "./styles.css"

const queryClient = new QueryClient()

let isSigningOutForAccessDenial = false

configureApiClient({
  baseUrl: import.meta.env.VITE_API_URL ?? "",
  onUnauthorized: () => {
    queryClient.clear()
    useAuthStore.getState().clearSession()
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.assign(buildRedirectUrl("/login", `${window.location.pathname}${window.location.search}`))
    }
  },
  onAccessDenied: () => {
    // Every request in flight is refused at once; sign out for the first refusal only.
    if (isSigningOutForAccessDenial) {
      return
    }
    isSigningOutForAccessDenial = true
    queryClient.clear()
    void useAuthStore
      .getState()
      .logout()
      .finally(() => window.location.assign(ACCESS_DENIED_LOGIN_URL))
  },
})

const router = createRouter({
  routeTree,
  context: {
    queryClient,
  },
  defaultPreload: "intent",
  scrollRestoration: true,
  defaultStructuralSharing: true,
  defaultPreloadStaleTime: 0,
  defaultErrorComponent: ErrorBoundary,
})

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

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
