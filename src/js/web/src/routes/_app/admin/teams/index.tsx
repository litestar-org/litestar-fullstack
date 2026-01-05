import { createFileRoute } from "@tanstack/react-router"
import { AdminNav } from "@/components/admin/admin-nav"
import { TeamTable } from "@/components/admin/team-table"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/admin/teams/")({
  component: AdminTeamsPage,
})

function AdminTeamsPage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Administration"
        title="Teams"
        description="View and manage all teams in the system."
      />
      <AdminNav />
      <PageSection>
        <TeamTable />
      </PageSection>
    </PageContainer>
  )
}
