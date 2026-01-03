import { createFileRoute } from "@tanstack/react-router"
import { RecentActivity } from "@/components/admin/recent-activity"
import { StatsCards } from "@/components/admin/stats-cards"

export const Route = createFileRoute("/_app/admin/")({
  component: AdminDashboardPage,
})

function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <StatsCards />
      <RecentActivity />
    </div>
  )
}
