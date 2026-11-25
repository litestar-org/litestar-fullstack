import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SkeletonCard } from "@/components/ui/skeleton"
import { getDashboardStatsOptions } from "@/lib/generated/api/@tanstack/react-query.gen"

export function StatsCards() {
  const { data: stats, isLoading, isError } = useQuery(getDashboardStatsOptions())

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: Static skeleton placeholders
          <SkeletonCard key={`stats-skeleton-${index}`} />
        ))}
      </div>
    )
  }

  if (isError || !stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Admin stats</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground">We could not load dashboard stats.</CardContent>
      </Card>
    )
  }

  const metrics = [
    { label: "Total users", value: stats.totalUsers },
    { label: "Active users", value: stats.activeUsers },
    { label: "Verified users", value: stats.verifiedUsers },
    { label: "Total teams", value: stats.totalTeams },
    { label: "New users today", value: stats.newUsersToday },
    { label: "New users this week", value: stats.newUsersWeek },
    { label: "Events today", value: stats.eventsToday },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <Card key={metric.label}>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">{metric.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">{metric.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
