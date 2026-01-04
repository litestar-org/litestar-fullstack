import { createFileRoute } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SkeletonCard } from "@/components/ui/skeleton"
import { useAdminTeam, useAdminUpdateTeam } from "@/lib/api/hooks/admin"

export const Route = createFileRoute("/_app/admin/teams/$teamId")({
  component: AdminTeamDetailPage,
})

function AdminTeamDetailPage() {
  const { teamId } = Route.useParams()
  const { data, isLoading, isError } = useAdminTeam(teamId)
  const updateTeam = useAdminUpdateTeam(teamId)

  if (isLoading) {
    return <SkeletonCard />
  }

  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Team detail</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">We could not load this team.</CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{data.name}</CardTitle>
      </CardHeader>
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
          <div className="md:col-span-2">
            <p className="text-muted-foreground">Description</p>
            <p>{data.description ?? "—"}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => updateTeam.mutate({ is_active: !data.isActive })} disabled={updateTeam.isPending}>
            {data.isActive ? "Deactivate" : "Activate"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
