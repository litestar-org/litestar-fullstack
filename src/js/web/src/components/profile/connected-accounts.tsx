import { Icons } from "@/components/icons"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuthConfig } from "@/lib/api/hooks/auth"
import { useAuthStore } from "@/lib/auth"

export function ConnectedAccounts() {
  const user = useAuthStore((state) => state.user)
  const { data: authConfig } = useAuthConfig()

  const accounts = user?.oauthAccounts ?? []
  const isGithubEnabled = authConfig?.githubEnabled ?? false

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connected accounts</CardTitle>
        <CardDescription>External OAuth providers linked to your account.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {accounts.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            {isGithubEnabled ? "No external accounts linked yet. Accounts created with GitHub sign-in appear here." : "No OAuth providers are currently enabled."}
          </p>
        ) : (
          <div className="space-y-3">
            {accounts.map((account) => (
              <div key={account.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
                <div className="flex items-center gap-3">
                  <Icons.GitHub className="h-4 w-4" />
                  <div>
                    <p className="font-medium capitalize">{account.oauthName}</p>
                    <p className="text-muted-foreground text-sm">{account.accountEmail}</p>
                  </div>
                </div>
                <Badge variant="secondary">Linked</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
