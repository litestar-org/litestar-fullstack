import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useParams } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { useEffect } from "react"
import { InviteMemberDialog } from "@/components/teams/invite-member-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/lib/auth"
import { getTeam, removeMemberFromTeam, type TeamMember } from "@/lib/generated/api"

export const Route = createFileRoute("/_app/teams/$teamId")({
  component: TeamDetail,
})

function TeamDetail() {
  const { teamId } = useParams({ from: "/_app/teams/$teamId" as const })
  const queryClient = useQueryClient()
  const { user, currentTeam, setCurrentTeam } = useAuthStore()

  const {
    data: team,
    isLoading: isTeamLoading,
    isError: isTeamError,
  } = useQuery({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await getTeam({ path: { team_id: teamId } })
      return response.data
    },
  })

  useEffect(() => {
    if (team && team.id !== currentTeam?.id) {
      setCurrentTeam(team)
    }
  }, [currentTeam?.id, setCurrentTeam, team])

  const removeMemberMutation = useMutation({
    mutationFn: (memberEmail: string) =>
      removeMemberFromTeam({
        path: { team_id: teamId },
        body: { userName: memberEmail },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", teamId] })
    },
  })

  if (isTeamLoading) {
    return (
      <PageContainer className="flex-1">
        <div className="text-muted-foreground">Loading team...</div>
      </PageContainer>
    )
  }

  if (isTeamError || !team) {
    return (
      <PageContainer className="flex-1">
        <div className="text-muted-foreground">
          {isTeamError ? "We couldn't load this team yet. Try refreshing." : "Team not found"}
        </div>
      </PageContainer>
    )
  }

  const members = team.members ?? []
  const ownerId = members.find((member) => member.isOwner)?.userId
  const canManageMembers = ownerId === user?.id || user?.isSuperuser || members.some((member) => member.userId === user?.id && member.role === "ADMIN")

  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Teams"
        title={team.name}
        description={team.description || "No description provided."}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" asChild>
              <Link to="/teams">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back
              </Link>
            </Button>
            {canManageMembers && <InviteMemberDialog teamId={teamId} />}
          </div>
        }
      />

      <PageSection>
        <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
          <Card className="border-border/60 bg-card/80 shadow-md shadow-primary/10">
            <CardHeader>
              <CardTitle>Members</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {members.map((member: TeamMember) => (
                <div key={member.id} className="flex items-center justify-between rounded-xl border border-border/60 bg-background/60 p-3">
                  <div className="flex flex-col">
                    <p className="font-medium text-foreground">{member.name ?? member.email}</p>
                    <p className="text-muted-foreground text-sm">{member.email}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="uppercase">
                      {member.role ?? "MEMBER"}
                    </Badge>
                    {canManageMembers && (
                      <Button variant="outline" size="sm" onClick={() => removeMemberMutation.mutate(member.email)}>
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
      </PageSection>
    </PageContainer>
  )
}

export default TeamDetail
