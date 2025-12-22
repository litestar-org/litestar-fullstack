import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Activity, AlertCircle, CheckCircle, Plus, Shield } from "lucide-react"
import { createFileRoute } from "@tanstack/react-router"
import { Link } from "@tanstack/react-router"
import { useEffect } from "react"
import { toast } from "sonner"

export const Route = createFileRoute("/_app/home")({
  component: HomePage,
})

function HomePage() {
  useEffect(() => {
    toast.message("Welcome back!", {
      description: "Deployment is healthy and queues are ready.",
    })
  }, [])

  return (
    <div className="flex-1 space-y-8 p-6 md:p-10">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Dashboard</p>
          <h1 className="font-['Space_Grotesk'] text-4xl font-semibold">Welcome back</h1>
          <p className="text-muted-foreground">Monitor service health, queues, and team activity at a glance.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" className="border-primary/40 text-primary" size="sm">
            <Shield className="mr-2 h-4 w-4" /> Security check
          </Button>
          <Button size="sm" asChild>
            <Link to="/teams/new">
              <Plus className="mr-2 h-4 w-4" /> Create team
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg">API Status</CardTitle>
            <CardDescription>Litestar service</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-primary" />
              <span className="font-semibold text-lg">Healthy</span>
            </div>
            <Badge variant="secondary">12ms p95</Badge>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg">Background Jobs</CardTitle>
            <CardDescription>SAQ queues</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-xl">0</p>
              <p className="text-muted-foreground text-sm">waiting jobs</p>
            </div>
            <Badge className="bg-secondary text-secondary-foreground">2 workers</Badge>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg">Active Teams</CardTitle>
            <CardDescription>Collaboration</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-xl">3</p>
              <p className="text-muted-foreground text-sm">teams live</p>
            </div>
            <Badge variant="outline">12 members</Badge>
          </CardContent>
        </Card>

        <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg">Alerts</CardTitle>
            <CardDescription>Deploy & auth</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-secondary" />
            <span className="text-sm text-muted-foreground">No new alerts</span>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Activity & releases</CardTitle>
              <CardDescription>Stay in sync with recent changes</CardDescription>
            </div>
            <Badge variant="outline" className="gap-1">
              <Activity className="h-3.5 w-3.5" /> Live
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs defaultValue="activity">
            <TabsList>
              <TabsTrigger value="activity">Activity</TabsTrigger>
              <TabsTrigger value="releases">Releases</TabsTrigger>
              <TabsTrigger value="checks">Checks</TabsTrigger>
            </TabsList>
            <TabsContent value="activity" className="space-y-3">
              {[
                { title: "Added OAuth callback route", meta: "2m ago · by you" },
                { title: "Generated SDK from OpenAPI", meta: "15m ago · CI" },
                { title: "SAQ worker scaled to 2 replicas", meta: "30m ago · autoscaler" },
              ].map((item) => (
                <div key={item.title} className="rounded-xl border border-border/60 bg-background/60 p-3">
                  <div className="font-medium text-foreground">{item.title}</div>
                  <div className="text-muted-foreground text-sm">{item.meta}</div>
                </div>
              ))}
            </TabsContent>
            <TabsContent value="releases" className="space-y-3">
              <div className="rounded-xl border border-border/60 bg-background/60 p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-foreground">v0.15.0-alpha.4</div>
                    <div className="text-muted-foreground text-sm">Litestar Vite integration & SPA handler fixes</div>
                  </div>
                  <Badge variant="secondary">Latest</Badge>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="checks" className="space-y-3">
              <div className="rounded-xl border border-border/60 bg-background/60 p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-foreground">Smoke tests</div>
                    <div className="text-muted-foreground text-sm">Routes, auth, queues</div>
                  </div>
                  <Badge className="bg-primary/20 text-primary">Passing</Badge>
                </div>
                <Separator className="my-3" />
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <span>API</span>
                  <span className="text-right text-foreground">OK</span>
                  <span>SPA bundle</span>
                  <span className="text-right text-foreground">OK</span>
                  <span>SAQ worker</span>
                  <span className="text-right text-foreground">OK</span>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
