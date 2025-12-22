import { createRootRoute, createRouter, Outlet } from "@tanstack/react-router"
export const Route = createRootRoute({
  component: RootRoute,
})

export const router = createRouter({
  routeTree: Route,
})

function RootRoute() {
  return <Outlet />
}
