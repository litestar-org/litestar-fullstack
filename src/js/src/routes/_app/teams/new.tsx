import { CreateTeamForm } from "@/components/teams/create-team-form"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/teams/new")({
  component: NewTeamPage,
})

function NewTeamPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="mb-8 font-bold text-3xl">Create New Team</h1>
      <CreateTeamForm />
    </div>
  )
}
