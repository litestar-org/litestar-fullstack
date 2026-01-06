import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useParams } from "@tanstack/react-router"
import { ArrowLeft, Clock, Mail, X } from "lucide-react"
import { useEffect } from "react"
import { InviteMemberDialog } from "@/components/teams/invite-member-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { Separator } from "@/components/ui/separator"
import { useAuthStore } from "@/lib/auth"
import { deleteTeamInvitation, getTeam, listTeamInvitations, removeMemberFromTeam, type TeamInvitation, type TeamMember } from "@/lib/generated/api"

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

  const { data: invitationsData } = useQuery({
    queryKey: ["teamInvitations", teamId],
    queryFn: async () => {
      const response = await listTeamInvitations({
        path: { team_id: teamId },
      })
      return response.data?.items ?? []
    },
    enabled: !!team,
  })

  const pendingInvitations = invitationsData?.filter((inv) => !inv.isAccepted) ?? []

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

  const cancelInvitationMutation = useMutation({
    mutationFn: (invitationId: string) =>
      deleteTeamInvitation({
        path: { team_id: teamId, invitation_id: invitationId },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teamInvitations", teamId] })
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
        <div className="text-muted-foreground">{isTeamError ? "We couldn't load this team yet. Try refreshing." : "Team not found"}</div>
      </PageContainer>
    )
  }

  const members = team.members ?? []
  const owner = members.find((member) => member.isOwner)
  const ownerId = owner?.userId
  const isOwner = ownerId === user?.id
  const canManageMembers = isOwner || user?.isSuperuser || members.some((member) => member.userId === user?.id && member.role === "ADMIN")

  const canRemoveMember = (member: TeamMember) => {
    // Cannot remove the owner (they must transfer ownership first)
    if (member.isOwner) return false
    // Cannot remove yourself unless you're superuser
    if (member.userId === user?.id && !user?.isSuperuser) return false
    return canManageMembers
  }

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
              {members.map((member: TeamMember) => {
                const isSelf = member.userId === user?.id
                return (
                  <div
                    key={member.id}
                    className={`flex items-center justify-between rounded-xl border bg-background/60 p-3 ${isSelf ? "border-primary/30 bg-primary/5" : "border-border/60"}`}
                  >
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">{member.name ?? member.email}</p>
                        {isSelf && (
                          <Badge variant="secondary" className="text-[10px]">
                            You
                          </Badge>
                        )}
                        {member.isOwner && <Badge className="text-[10px]">Owner</Badge>}
                      </div>
                      <p className="text-muted-foreground text-sm">{member.email}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="uppercase">
                        {member.role ?? "MEMBER"}
                      </Badge>
                      {canRemoveMember(member) && (
                        <Button variant="outline" size="sm" onClick={() => removeMemberMutation.mutate(member.email)}>
                          Remove
                        </Button>
                      )}
                    </div>
                  </div>
                )
              })}
              {members.length === 0 && <div className="text-muted-foreground text-sm">No members yet.</div>}

              {/* Pending Invitations */}
              {pendingInvitations.length > 0 && (
                <>
                  <Separator className="my-4" />
                  <div className="space-y-2">
                    <p className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      Pending invitations
                    </p>
                    {pendingInvitations.map((invitation: TeamInvitation) => (
                      <div key={invitation.id} className="flex items-center justify-between rounded-lg border border-dashed border-border/60 bg-muted/30 p-3">
                        <div className="flex items-center gap-3">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-sm font-medium">{invitation.email}</p>
                            <p className="text-xs text-muted-foreground">Invited as {invitation.role.toLowerCase()}</p>
                          </div>
                        </div>
                        {canManageMembers && (
                          <Button variant="ghost" size="sm" onClick={() => cancelInvitationMutation.mutate(invitation.id)}>
                            <X className="h-4 w-4" />
                            <span className="sr-only">Cancel invitation</span>
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
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
