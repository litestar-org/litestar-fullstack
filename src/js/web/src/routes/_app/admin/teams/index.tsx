import { createFileRoute } from "@tanstack/react-router"
import { TeamTable } from "@/components/admin/team-table"

export const Route = createFileRoute("/_app/admin/teams/")({
  component: AdminTeamsPage,
})

function AdminTeamsPage() {
  return <TeamTable />
}
