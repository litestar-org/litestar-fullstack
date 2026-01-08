import { createFileRoute } from "@tanstack/react-router"
import { ChevronRight, Shield, Tag, UserPlus, Users } from "lucide-react"
import { CreateTeamForm } from "@/components/teams/create-team-form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer, PageHeader } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/teams/new")({
  component: NewTeamPage,
})

const tips = [
  {
    icon: Users,
    title: "Collaborate together",
    description: "Group members and share resources",
  },
  {
    icon: Shield,
    title: "Role-based access",
    description: "Control what members can do",
  },
  {
    icon: UserPlus,
    title: "Invite members",
    description: "Add people by email",
  },
  {
    icon: Tag,
    title: "Organize with tags",
    description: "Categorize for easy discovery",
  },
]

function NewTeamPage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader eyebrow="Teams" title="Create New Team" description="Set up a new team to organize members and manage access." />

      <div className="flex gap-6">
        {/* Main form */}
        <Card className="min-w-0 flex-1">
          <CardHeader>
            <CardTitle className="text-lg">Team Details</CardTitle>
          </CardHeader>
          <CardContent>
            <CreateTeamForm />
          </CardContent>
        </Card>

        {/* Sidebar tips - styled like Quick Actions */}
        <Card className="h-fit w-72 shrink-0 border-border/40 bg-linear-to-br from-muted/30 to-muted/10">
          <CardHeader className="space-y-1 pb-3">
            <CardTitle className="text-lg">Getting Started</CardTitle>
            <CardDescription>Tips for your new team</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {tips.map((tip) => (
              <div key={tip.title} className="group flex items-center gap-3 rounded-lg bg-background/60 p-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <tip.icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm">{tip.title}</p>
                  <p className="text-xs text-muted-foreground">{tip.description}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground/30" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
