import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router"
import { CheckCircle, Users, XCircle } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer } from "@/components/ui/page-layout"
import { acceptTeamInvitation, getTeam, rejectTeamInvitation } from "@/lib/generated/api"

export const Route = createFileRoute("/_app/teams/$teamId/invitations/$invitationId/accept")({
  component: AcceptInvitationPage,
})

function AcceptInvitationPage() {
  const navigate = useNavigate()
  const { teamId, invitationId } = useParams({
    from: "/_app/teams/$teamId/invitations/$invitationId/accept",
  })
  const [status, setStatus] = useState<"pending" | "accepting" | "declining" | "accepted" | "declined" | "error">("pending")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Optionally fetch team info for display
  const { data: team, isLoading: isTeamLoading } = useQuery({
    queryKey: ["team", teamId],
    queryFn: async () => {
      const response = await getTeam({ path: { team_id: teamId } })
      return response.data
    },
  })

  const acceptMutation = useMutation({
    mutationFn: async () => {
      const response = await acceptTeamInvitation({
        path: { team_id: teamId, invitation_id: invitationId },
      })
      if (response.error) {
        throw new Error(response.error.detail || "Failed to accept invitation")
      }
      return response.data
    },
    onMutate: () => {
      setStatus("accepting")
      setErrorMessage(null)
    },
    onSuccess: () => {
      setStatus("accepted")
      toast.success("You've joined the team!")
      // Navigate to the team page after a short delay
      setTimeout(() => {
        navigate({ to: "/teams/$teamId", params: { teamId } })
      }, 1500)
    },
    onError: (error: Error) => {
      setStatus("error")
      setErrorMessage(error.message)
      toast.error("Failed to accept invitation", {
        description: error.message,
      })
    },
  })

  const declineMutation = useMutation({
    mutationFn: async () => {
      const response = await rejectTeamInvitation({
        path: { team_id: teamId, invitation_id: invitationId },
      })
      if (response.error) {
        throw new Error(response.error.detail || "Failed to decline invitation")
      }
      return response.data
    },
    onMutate: () => {
      setStatus("declining")
      setErrorMessage(null)
    },
    onSuccess: () => {
      setStatus("declined")
      toast.success("Invitation declined")
      // Navigate to teams list after a short delay
      setTimeout(() => {
        navigate({ to: "/teams" })
      }, 1500)
    },
    onError: (error: Error) => {
      setStatus("error")
      setErrorMessage(error.message)
      toast.error("Failed to decline invitation", {
        description: error.message,
      })
    },
  })

  const isPending = status === "pending"
  const isProcessing = status === "accepting" || status === "declining"
  const isComplete = status === "accepted" || status === "declined"

  return (
    <PageContainer className="flex flex-1 items-center justify-center">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            {status === "accepted" ? (
              <CheckCircle className="h-6 w-6 text-success" />
            ) : status === "declined" ? (
              <XCircle className="h-6 w-6 text-muted-foreground" />
            ) : (
              <Users className="h-6 w-6 text-primary" />
            )}
          </div>
          <CardTitle>{status === "accepted" ? "Welcome to the team!" : status === "declined" ? "Invitation declined" : "Team Invitation"}</CardTitle>
          <CardDescription>
            {status === "accepted" ? (
              "You're now a member. Redirecting..."
            ) : status === "declined" ? (
              "You won't be added to this team."
            ) : isTeamLoading ? (
              "Loading invitation details..."
            ) : team ? (
              <>
                You've been invited to join <strong>{team.name}</strong>
              </>
            ) : (
              "You've been invited to join a team"
            )}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {status === "error" && errorMessage && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          {isProcessing && (
            <div className="flex flex-col items-center space-y-3 py-4">
              <Icons.spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">{status === "accepting" ? "Joining team..." : "Declining invitation..."}</p>
            </div>
          )}

          {isComplete && (
            <div className="flex flex-col items-center space-y-3 py-4">
              <Icons.spinner className="h-6 w-6 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Redirecting...</p>
            </div>
          )}
        </CardContent>

        {(isPending || status === "error") && (
          <CardFooter className="flex flex-col gap-2">
            <Button className="w-full" onClick={() => acceptMutation.mutate()} disabled={isProcessing}>
              Accept Invitation
            </Button>
            <Button variant="outline" className="w-full" onClick={() => declineMutation.mutate()} disabled={isProcessing}>
              Decline
            </Button>
          </CardFooter>
        )}
      </Card>
    </PageContainer>
  )
}
