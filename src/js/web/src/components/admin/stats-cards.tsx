import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SkeletonCard } from "@/components/ui/skeleton"
import { useAdminDashboardStats } from "@/lib/api/hooks/admin"

export function StatsCards() {
  const { data, isLoading, isError } = useAdminDashboardStats()

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <SkeletonCard key={`stats-skeleton-${index}`} />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Admin stats</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">We could not load dashboard stats.</CardContent>
      </Card>
    )
  }

  const items = [
    { label: "Total users", value: data.total_users },
    { label: "Active users", value: data.active_users },
    { label: "Verified users", value: data.verified_users },
    { label: "Total teams", value: data.total_teams },
    { label: "New users today", value: data.new_users_today },
    { label: "New users this week", value: data.new_users_week },
    { label: "Events today", value: data.events_today },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">{item.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{item.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
