import { Badge } from "@/components/ui/badge"
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
    return <div className="text-muted-foreground">Loading teams…</div>
  }

  if (teams.length === 0) {
    return (
      <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
        <CardHeader>
          <CardTitle className="text-2xl">Create your first team</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            Organize members, roles, and invitations in one place. Teams drive access control across the app.
          </p>
          <Button asChild>
            <Link to="/teams/new">Create team</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-['Space_Grotesk'] text-2xl font-semibold">Teams</h2>
          <p className="text-muted-foreground">Switch context or drill into membership quickly.</p>
        </div>
        <Button asChild>
          <Link to="/teams/new">New team</Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {teams.map((team: Team) => {
          const active = currentTeam?.id === team.id
          return (
            <Card key={team.id} className={`border-border/60 bg-card/80 shadow-md ${active ? "border-primary/60 shadow-primary/15" : ""}`}>
              <CardHeader className="space-y-2">
                <div className="flex items-center justify-between">
                  <CardTitle>{team.name}</CardTitle>
                  {active && <Badge variant="secondary">Current</Badge>}
                </div>
                <p className="text-muted-foreground text-sm line-clamp-2">{team.description || "No description provided."}</p>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                <Button variant={active ? "default" : "outline"} size="sm" onClick={() => setCurrentTeam(team)}>
                  {active ? "Active" : "Switch"}
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link to={"/teams/$teamId" as const} params={{ teamId: team.id }}>
                    View
                  </Link>
                </Button>
              </CardContent>
            </Card>
          )
        })}
        <Card className="border-dashed border-border/60 bg-card/60">
          <CardHeader>
            <CardTitle>Create New Team</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-muted-foreground text-sm">Spin up a space for a client, squad, or internal initiative.</p>
            <Button asChild variant="secondary">
              <Link to="/teams/new">Start a team</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
