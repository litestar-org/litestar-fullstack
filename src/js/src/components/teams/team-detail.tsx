import { useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TeamManagement } from "./team-management";

export function TeamDetail() {
  const { teamId } = useParams();

  const { data: team, isLoading } = useQuery({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await api.teams.get(teamId);
      return response.data;
    },
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!team) {
    return <div>Team not found</div>;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{team.name}</CardTitle>
        </CardHeader>
        <CardContent>
          {team.description && <p>{team.description}</p>}
        </CardContent>
      </Card>

      <TeamManagement />
    </div>
  );
}
