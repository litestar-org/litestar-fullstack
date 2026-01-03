import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useAdminRecentActivity } from "@/lib/api/hooks/admin"

export function RecentActivity() {
  const { data, isLoading, isError } = useAdminRecentActivity()

  if (isLoading) {
    return <SkeletonTable rows={4} />
  }

  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">We could not load recent activity.</CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.activities.length === 0 && (
          <p className="text-muted-foreground text-sm">No recent activity yet.</p>
        )}
        {data.activities.map((activity) => (
          <div key={activity.id} className="flex flex-col gap-1 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium">{activity.action}</p>
              <span className="text-xs text-muted-foreground">
                {new Date(activity.created_at).toLocaleString()}
              </span>
            </div>
            <div className="text-muted-foreground text-sm">
              {activity.actor_email ?? "System"} {activity.target_label ? `• ${activity.target_label}` : ""}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
