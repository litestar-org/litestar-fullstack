import { createFileRoute } from "@tanstack/react-router";
import { useToast } from "@/hooks/use-toast";
import { useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const Route = createFileRoute("/_app/home")({
  component: HomePage,
});

function HomePage() {
  const { toast } = useToast();

  useEffect(() => {
    toast({
      title: "Welcome back!",
      description: "We're glad to see you again.",
    });
  }, [toast]);

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold">Welcome to Team Manager</h1>
        <p className="text-muted-foreground">
          Your central hub for managing teams and projects
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
            <CardDescription>Overview of your teams</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-2xl font-bold">3</p>
              <p className="text-sm text-muted-foreground">Active Teams</p>
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
              <p className="text-xs text-muted-foreground">2 hours ago</p>
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
  );
}
