import { Outlet, createRootRoute, createRouter } from "@tanstack/react-router"

export const Route = createRootRoute({
  component: RootRoute,
})

export const router = createRouter({
  routeTree: Route,
})

function RootRoute() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto py-4">
        <Outlet />
      </main>
    </div>
  )
}
