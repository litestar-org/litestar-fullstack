import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"
import { AdminNav } from "@/components/admin/admin-nav"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { SkeletonCard } from "@/components/ui/skeleton"
import { extractApiErrorMessage } from "@/lib/api-client"
import { adminGetTeamOptions, adminGetTeamQueryKey, adminListTeamsQueryKey, adminUpdateTeamMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export const Route = createFileRoute("/_app/admin/teams/$teamId")({
  component: AdminTeamDetailPage,
})

function AdminTeamDetailPage() {
  const { teamId } = Route.useParams()
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    ...adminGetTeamOptions({ path: { team_id: teamId } }),
    enabled: Boolean(teamId),
  })
  const updateTeam = useMutation({
    ...adminUpdateTeamMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminListTeamsQueryKey() })
      queryClient.invalidateQueries({ queryKey: adminGetTeamQueryKey({ path: { team_id: teamId } }) })
      toast.success("Team updated")
    },
    onError: (error) => {
      toast.error("Unable to update team", {
        description: extractApiErrorMessage(error, "Try again later"),
      })
    },
  })

  if (isLoading) {
    return (
      <PageContainer className="flex-1 space-y-8">
        <PageHeader eyebrow="Administration" title="Team Details" />
        <AdminNav />
        <PageSection>
          <SkeletonCard />
        </PageSection>
      </PageContainer>
    )
  }

  if (isError || !data) {
    return (
      <PageContainer className="flex-1 space-y-8">
        <PageHeader
          eyebrow="Administration"
          title="Team Details"
          actions={
            <Button variant="outline" size="sm" asChild>
              <Link to="/admin/teams">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to teams
              </Link>
            </Button>
          }
        />
        <AdminNav />
        <PageSection>
          <Card>
            <CardHeader>
              <CardTitle>Team detail</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">We could not load this team.</CardContent>
          </Card>
        </PageSection>
      </PageContainer>
    )
  }

  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Administration"
        title={data.name}
        description={data.description || "No description provided."}
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link to="/admin/teams">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to teams
            </Link>
          </Button>
        }
      />
      <AdminNav />
      <PageSection>
        <Card>
          <CardContent className="space-y-4">
            <div className="grid gap-3 text-sm md:grid-cols-2">
              <div>
                <p className="text-muted-foreground">Slug</p>
                <p>{data.slug}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Owner</p>
                <p>{data.ownerEmail ?? "—"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Members</p>
                <p>{data.memberCount ?? 0}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p>{data.isActive ? "Active" : "Inactive"}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => updateTeam.mutate({ path: { team_id: teamId }, body: { isActive: !data.isActive } })} disabled={updateTeam.isPending}>
                {data.isActive ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </PageSection>
    </PageContainer>
  )
}
