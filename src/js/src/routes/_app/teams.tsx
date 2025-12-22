import { Outlet, createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/teams")({
  component: TeamsLayout,
})

function TeamsLayout() {
  return <Outlet />
}

export default TeamsLayout
