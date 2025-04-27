import { createFileRoute, useParams } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, TeamMember } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Button } from '@/components/ui/button'

export const Route = createFileRoute('/_app/teams/$teamId')({
  component: TeamComponent,
})

function TeamComponent() {
  const { teamId } = useParams({ from: Route });
  const { currentTeam } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: team, isLoading: isTeamLoading } = useQuery({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await api.teams.get(teamId);
      return response.data;
    },
  });

  const { data: members = [], isLoading: isMembersLoading } = useQuery({
    queryKey: ["team-members", teamId],
    queryFn: async () => {
      const response = await api.teams.members.list(teamId);
      return response.data;
    },
  });

  const addMemberMutation = useMutation({
    mutationFn: async (email: string) => {
      const response = await api.teams.members.add(teamId, {
        email,
        role: "member",
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members", teamId] });
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: async (memberId: string) => {
      await api.teams.members.remove(teamId, memberId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members", teamId] });
    },
  });

  if (isTeamLoading || isMembersLoading) {
    return <div>Loading...</div>;
  }

  const canManageMembers = team?.permissions.includes("manage_members");

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        {canManageMembers && (
          <Button onClick={() => addMemberMutation.mutate("")}>
            Add Member
          </Button>
        )}
      </div>
      <div className="grid gap-4">
        {members.map((member: TeamMember) => (
          <div key={member.id} className="flex items-center justify-between">
            <div>
              <p className="font-medium">{member.name}</p>
              <p className="text-sm text-muted-foreground">{member.email}</p>
            </div>
            {canManageMembers && (
              <Button
                variant="destructive"
                onClick={() => removeMemberMutation.mutate(member.id)}
              >
                Remove
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default TeamComponent;
