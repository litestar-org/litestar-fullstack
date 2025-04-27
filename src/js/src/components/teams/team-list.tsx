import { useTeam } from "@/lib/team-context";
import { useQuery } from "@tanstack/react-query";
import { Team } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "@tanstack/react-router";
import { listTeams } from '@/lib/api/sdk.gen'

export function TeamList() {
  const { currentTeam, setCurrentTeam } = useTeam();

  const { data: teams = [], isLoading } = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const response = await listTeams();
      return response.data?.items ?? [];
    },
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (teams.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Teams</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">
            You don&apos;t have any teams yet. Create your first team to get started.
          </p>
          <Button asChild>
            <Link to="/teams/new">Create Team</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {teams.map((team: Team) => (
        <Card
          key={team.id}
          className={currentTeam?.id === team.id ? "border-primary" : ""}
        >
          <CardHeader>
            <CardTitle>{team.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button
                variant={currentTeam?.id === team.id ? "default" : "outline"}
                onClick={() => setCurrentTeam(team)}
              >
                {currentTeam?.id === team.id ? "Current Team" : "Switch to Team"}
              </Button>
              <Button variant="outline" asChild>
                <Link to={`/teams/$teamId` as const} params={{ teamId: team.id }}>View Team</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
      <Card>
        <CardHeader>
          <CardTitle>Create New Team</CardTitle>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link to="/teams/new">Create Team</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
