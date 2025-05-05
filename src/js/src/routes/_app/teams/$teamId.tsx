// import { useAuthStore } from "@/lib/auth";
import { Button } from "@/components/ui/button"
import type { TeamMember } from "@/lib/api"
import { addMemberToTeam, getTeam, listTeams, removeMemberFromTeam } from "@/lib/api/sdk.gen"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useParams } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/teams/$teamId")({
  component: TeamDetail,
})

function TeamDetail() {
  const { teamId } = useParams({ from: "/_app/teams/$teamId" as const })
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  // const { currentTeam } = useAuthStore();
  const queryClient = useQueryClient()

  const { data: team, isLoading: isTeamLoading } = useQuery({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await getTeam({ path: { team_id: teamId } })
      return response.data
    },
  })

  const { data: members = [], isLoading: isMembersLoading } = useQuery({
    queryKey: ["team-members", teamId],
    queryFn: async () => {
      const response = await listTeams({ query: { ids: [teamId] } })
      return response.data?.items?.[0]?.members ?? []
    },
  })

  const addMemberMutation = useMutation({
    mutationFn: (email: string) => addMemberToTeam({ path: { team_id: teamId }, body: { userName: email } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members", teamId] })
    },
  })

  const removeMemberMutation = useMutation({
    mutationFn: (memberId: string) =>
      removeMemberFromTeam({
        path: { team_id: teamId },
        body: { userName: memberId },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members", teamId] })
    },
  })

  if (isTeamLoading || isMembersLoading) {
    return <div>Loading...</div>
  }

  if (!team) {
    return <div>Team not found</div>
  }

  const canManageMembers = members.some((member) => member.role === "ADMIN")

  return (
    <div className="container mx-auto py-8">
      <h1 className="mb-4 font-bold text-2xl">{team.name}</h1>
      <p className="text-gray-600">{team.description}</p>
      <div className="space-y-6">
        <div className="flex justify-end">{canManageMembers && <Button onClick={() => addMemberMutation.mutate("")}>Add Member</Button>}</div>
        <div className="grid gap-4">
          {members.map((member: TeamMember) => (
            <div key={member.id} className="flex items-center justify-between">
              <div>
                <p className="font-medium">{member.name}</p>
                <p className="text-muted-foreground text-sm">{member.email}</p>
              </div>
              {canManageMembers && (
                <Button variant="destructive" onClick={() => removeMemberMutation.mutate(member.id)}>
                  Remove
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TeamDetail
