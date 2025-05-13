import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/home")({
  component: HomePage,
})

function HomePage() {
  return (
    <div className="flex-1 p-8">
      <div className="space-y-2">
        <h1 className="font-bold text-4xl">Welcome to Team Manager</h1>
        <p className="text-muted-foreground">Your central hub for managing teams and projects</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
            <CardDescription>Overview of your teams</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="font-bold text-2xl">3</p>
              <p className="text-muted-foreground text-sm">Active Teams</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest updates in your teams</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm">New team member added to Project Alpha</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>What's New</CardTitle>
            <CardDescription>Latest features and updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm">• Enhanced team collaboration tools</p>
              <p className="text-sm">• Improved performance dashboard</p>
              <p className="text-sm">• New team analytics features</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
