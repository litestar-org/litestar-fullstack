import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { Team } from "@/lib/api"
import { listTeams } from "@/lib/api/sdk.gen"
import { useTeam } from "@/lib/team-context"
import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

export function TeamList() {
  const { currentTeam, setCurrentTeam } = useTeam()

  const { data: teams = [], isLoading } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await listTeams()
      return response.data?.items ?? []
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (teams.length === 0) {
    return (
      <div className="mt-12 flex w-full justify-center">
        <Card className="h-fit w-fit">
          <CardHeader>
            <CardTitle>No Teams</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-muted-foreground">You don&apos;t have any teams yet. Create your first team to get started.</p>
            <Button asChild>
              <Link to="/teams/new">Create Team</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex h-full w-full gap-4 rounded-lg bg-accent p-4">
      {teams.map((team: Team) => (
        <div
          key={team.id}
          className={`h-fit w-full rounded-xl border border-transparent ${currentTeam?.id === team.id ? "animate-gradient bg-gradient-to-r from-orange-700 via-blue-500 to-green-400" : ""}`}
        >
          <Card className="overflow-auto">
            <CardHeader>
              <CardTitle>{team.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button variant={currentTeam?.id === team.id ? "default" : "outline"} onClick={() => setCurrentTeam(team)}>
                  {currentTeam?.id === team.id ? "Current Team" : "Switch to Team"}
                </Button>
                <Button variant="outline" asChild>
                  <Link to={"/teams/$teamId" as const} params={{ teamId: team.id }}>
                    View Team
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      ))}
    </div>
  )
}
