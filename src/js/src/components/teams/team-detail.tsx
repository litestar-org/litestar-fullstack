import { useParams } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { getTeam } from '@/lib/api/sdk.gen'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TeamManagement } from "./team-management";

export function TeamDetail() {
  const { teamId } = useParams({ from: '/_app/teams/$teamId' as const });

  const { data: team, isLoading } = useQuery({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await getTeam({ path: { team_id: teamId } });
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
