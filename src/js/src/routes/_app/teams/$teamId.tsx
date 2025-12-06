// import { useAuthStore } from "@/lib/auth";
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
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
    return <div className="text-muted-foreground">Loading team…</div>
  }

  if (!team) {
    return <div className="text-muted-foreground">Team not found</div>
  }

  const canManageMembers = members.some((member) => member.role === "ADMIN")
  const initials = team.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)

  return (
    <div className="container mx-auto space-y-6 py-8">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-12 w-12 bg-primary/20 text-primary">
            <AvatarFallback className="text-lg font-semibold text-primary">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <h1 className="font-['Space_Grotesk'] text-3xl font-semibold">{team.name}</h1>
            <p className="text-muted-foreground">{team.description || "No description provided."}</p>
          </div>
        </div>
        {canManageMembers && (
          <Button onClick={() => addMemberMutation.mutate("")} className="w-full md:w-auto">
            Add member
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-border/60 bg-card/80 shadow-md shadow-primary/10">
          <CardHeader>
            <CardTitle>Members</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {members.map((member: TeamMember) => (
              <div key={member.id} className="flex items-center justify-between rounded-xl border border-border/60 bg-background/60 p-3">
                <div className="flex flex-col">
                  <p className="font-medium text-foreground">{member.name}</p>
                  <p className="text-muted-foreground text-sm">{member.email}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="uppercase">
                    {member.role ?? "MEMBER"}
                  </Badge>
                  {canManageMembers && (
                    <Button variant="outline" size="sm" onClick={() => removeMemberMutation.mutate(member.id)}>
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            ))}
            {members.length === 0 && <div className="text-muted-foreground text-sm">No members yet.</div>}
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card/80 shadow-md shadow-primary/10">
          <CardHeader>
            <CardTitle>Team overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="flex justify-between text-foreground">
              <span>Member count</span>
              <Badge variant="secondary">{members.length}</Badge>
            </div>
            <Separator className="my-3" />
            <p>Use this space to track key links, environments, or runbooks for the team.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default TeamDetail
