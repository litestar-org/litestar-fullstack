import { useQuery } from "@tanstack/react-query"
import { Icons } from "@/components/icons"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuthStore } from "@/lib/auth"
import { publicAuthConfigOptions } from "@/lib/generated/api/@tanstack/react-query.gen"

export function ConnectedAccounts() {
  const user = useAuthStore((state) => state.user)
  const { data: authConfig } = useQuery({
    ...publicAuthConfigOptions(),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  const accounts = user?.oauthAccounts ?? []
  const enabledProviders = [authConfig?.githubEnabled ? "GitHub" : null, authConfig?.googleEnabled ? "Google" : null].filter(Boolean)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connected accounts</CardTitle>
        <CardDescription>External OAuth providers linked to your account.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {accounts.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            {enabledProviders.length > 0
              ? `No external accounts linked yet. Sign in with ${enabledProviders.join(" or ")} on the login page to associate a provider.`
              : "No OAuth providers are currently enabled."}
          </p>
        ) : (
          <div className="space-y-3">
            {accounts.map((account) => {
              const provider = account.oauthName.toLowerCase()
              const Icon = provider === "google" ? Icons.google : Icons.gitHub
              return (
                <div key={account.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
                  <div className="flex items-center gap-3">
                    <Icon className="h-4 w-4" />
                    <div>
                      <p className="font-medium capitalize">{account.oauthName}</p>
                      <p className="text-muted-foreground text-sm">{account.accountEmail}</p>
                    </div>
                  </div>
                  <Badge variant="secondary">Linked</Badge>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
