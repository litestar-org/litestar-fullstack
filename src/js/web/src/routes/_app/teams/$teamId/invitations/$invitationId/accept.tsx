import { useMutation, useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router"
import { CheckCircle, Users, XCircle } from "lucide-react"
import { type ReactNode, useEffect, useState } from "react"
import { toast } from "sonner"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer } from "@/components/ui/page-layout"
import { extractApiErrorMessage } from "@/lib/api-client"
import type { Team } from "@/lib/generated/api"
import { acceptTeamInvitationMutation, getTeamOptions, rejectTeamInvitationMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export const Route = createFileRoute("/_app/teams/$teamId/invitations/$invitationId/accept")({
  component: AcceptInvitationPage,
})

const REDIRECT_DELAY_MS = 1500

type InvitationStatus = "pending" | "accepting" | "declining" | "accepted" | "declined" | "error"

interface InvitationHeading {
  icon: ReactNode
  title: string
  description: ReactNode
}

function describeInvitation(team: Team | undefined, isTeamLoading: boolean): ReactNode {
  if (isTeamLoading) {
    return "Loading invitation details..."
  }
  if (!team) {
    return "You've been invited to join a team"
  }
  return (
    <>
      You've been invited to join <strong>{team.name}</strong>
    </>
  )
}

function resolveHeading(status: InvitationStatus, team: Team | undefined, isTeamLoading: boolean): InvitationHeading {
  if (status === "accepted") {
    return {
      icon: <CheckCircle className="h-6 w-6 text-success" />,
      title: "Welcome to the team!",
      description: "You're now a member. Redirecting...",
    }
  }
  if (status === "declined") {
    return {
      icon: <XCircle className="h-6 w-6 text-muted-foreground" />,
      title: "Invitation declined",
      description: "You won't be added to this team.",
    }
  }
  return {
    icon: <Users className="h-6 w-6 text-primary" />,
    title: "Team Invitation",
    description: describeInvitation(team, isTeamLoading),
  }
}

function AcceptInvitationPage() {
  const navigate = useNavigate()
  const { teamId, invitationId } = useParams({
    from: "/_app/teams/$teamId/invitations/$invitationId/accept",
  })
  const [status, setStatus] = useState<InvitationStatus>("pending")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // The team name only decorates the prompt, so a failed lookup is not retried.
  const { data: team, isLoading: isTeamLoading } = useQuery({
    ...getTeamOptions({ path: { team_id: teamId } }),
    retry: false,
  })

  const acceptInvitation = useMutation({
    ...acceptTeamInvitationMutation(),
    onMutate: () => {
      setStatus("accepting")
      setErrorMessage(null)
    },
    onSuccess: () => {
      setStatus("accepted")
      toast.success("You've joined the team!")
    },
    onError: (error) => {
      const message = extractApiErrorMessage(error, "Failed to accept invitation")
      setStatus("error")
      setErrorMessage(message)
      toast.error("Failed to accept invitation", { description: message })
    },
  })

  const declineInvitation = useMutation({
    ...rejectTeamInvitationMutation(),
    onMutate: () => {
      setStatus("declining")
      setErrorMessage(null)
    },
    onSuccess: () => {
      setStatus("declined")
      toast.success("Invitation declined")
    },
    onError: (error) => {
      const message = extractApiErrorMessage(error, "Failed to decline invitation")
      setStatus("error")
      setErrorMessage(message)
      toast.error("Failed to decline invitation", { description: message })
    },
  })

  useEffect(() => {
    if (status !== "accepted" && status !== "declined") {
      return
    }
    const redirectTimer = setTimeout(() => {
      if (status === "accepted") {
        void navigate({ to: "/teams/$teamId", params: { teamId } })
      } else {
        void navigate({ to: "/teams" })
      }
    }, REDIRECT_DELAY_MS)
    return () => clearTimeout(redirectTimer)
  }, [status, navigate, teamId])

  const invitationPath = { team_id: teamId, invitation_id: invitationId }
  const canRespond = status === "pending" || status === "error"
  const isProcessing = status === "accepting" || status === "declining"
  const isComplete = status === "accepted" || status === "declined"
  const heading = resolveHeading(status, team, isTeamLoading)

  return (
    <PageContainer className="flex flex-1 items-center justify-center">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">{heading.icon}</div>
          <CardTitle>{heading.title}</CardTitle>
          <CardDescription>{heading.description}</CardDescription>
        </CardHeader>

        <CardContent>
          {status === "error" && errorMessage && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          {isProcessing && (
            <div className="flex flex-col items-center space-y-3 py-4">
              <Icons.Spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">{status === "accepting" ? "Joining team..." : "Declining invitation..."}</p>
            </div>
          )}

          {isComplete && (
            <div className="flex flex-col items-center space-y-3 py-4">
              <Icons.Spinner className="h-6 w-6 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Redirecting...</p>
            </div>
          )}
        </CardContent>

        {canRespond && (
          <CardFooter className="flex flex-col gap-2">
            <Button className="w-full" onClick={() => acceptInvitation.mutate({ path: invitationPath })} disabled={isProcessing}>
              Accept Invitation
            </Button>
            <Button variant="outline" className="w-full" onClick={() => declineInvitation.mutate({ path: invitationPath })} disabled={isProcessing}>
              Decline
            </Button>
          </CardFooter>
        )}
      </Card>
    </PageContainer>
  )
}
