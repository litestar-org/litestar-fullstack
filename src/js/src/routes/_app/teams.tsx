import { Button } from "@/components/ui/button"
// import type { Team } from "@/lib/api"
import { listTeams } from "@/lib/api/sdk.gen"
import { useAuthStore } from "@/lib/auth"
import { useQuery } from "@tanstack/react-query"
import { Outlet, createFileRoute } from "@tanstack/react-router"
import { Link } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/teams")({
  component: Teams,
})

function Teams() {
  const { currentTeam, setCurrentTeam, teams, setTeams } = useAuthStore()

  const { data: teamsData = [], isLoading } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await listTeams()
      return response.data?.items ?? []
    },
  })

  if (teamsData.length > 0 && teams.length === 0) {
    setTeams(teamsData)
    if (!currentTeam) {
      setCurrentTeam(teamsData[0])
    }
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div className="flex h-full w-full flex-col">
      <div className="m-4 flex items-center justify-between">
        <h1 className="font-bold text-2xl">Teams Home Page</h1>
        <Button asChild>
          <Link to="/teams/new">Create Team</Link>
        </Button>
      </div>
      <div className="m-4 flex flex-1">
        <Outlet />
      </div>
      {/* NOTE: enable when needed */}
      {/* <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {teamsData.map((team: Team) => (
          <div key={team.id} className="rounded-lg border p-4">
            <h2 className="mb-2 font-semibold text-xl">{team.name}</h2>
            <p className="mb-4 text-gray-600">{team.description}</p>
            <div className="flex gap-2">
              <Button asChild>
                <Link to={"/teams/$teamId" as const} params={{ teamId: team.id }}>
                  View Team
                </Link>
              </Button>
            </div>
          </div>
        ))}
      </div> */}
    </div>
  )
}

export default Teams
