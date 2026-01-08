import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { TeamList } from "@/components/teams/team-list"
import { Button } from "@/components/ui/button"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/teams/")({
  component: TeamsPage,
})

function TeamsPage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Teams"
        description="Manage your teams and collaborate with members."
        actions={
          <Button size="sm" asChild>
            <Link to="/teams/new">
              <Plus className="mr-2 h-4 w-4" /> New team
            </Link>
          </Button>
        }
      />
      <PageSection>
        <TeamList />
      </PageSection>
    </PageContainer>
  )
}
