import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { CreateTeamForm } from "@/components/teams/create-team-form"
import { Button } from "@/components/ui/button"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/teams/new")({
  component: NewTeamPage,
})

function NewTeamPage() {
  return (
    <PageContainer className="flex-1 space-y-8" maxWidth="lg">
      <PageHeader
        eyebrow="Teams"
        title="Create New Team"
        description="Set up a new team to organize members and manage access."
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link to="/teams">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to teams
            </Link>
          </Button>
        }
      />
      <PageSection>
        <CreateTeamForm />
      </PageSection>
    </PageContainer>
  )
}
