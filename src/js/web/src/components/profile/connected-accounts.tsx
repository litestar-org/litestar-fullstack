import { useMemo } from "react"
import { toast } from "sonner"
import { Icons } from "@/components/icons"
import { OAuthLinkButton } from "@/components/profile/oauth-link-button"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { SkeletonCard } from "@/components/ui/skeleton"
import { useOAuthAccounts, useStartOAuthLink, useUnlinkOAuthAccount } from "@/lib/api/hooks/auth"
import { useOAuthConfig } from "@/hooks/use-oauth-config"

export function ConnectedAccounts() {
  const { data, isLoading, isError } = useOAuthAccounts()
  const { data: oauthConfig } = useOAuthConfig()
  const startLink = useStartOAuthLink()
  const unlink = useUnlinkOAuthAccount()

  const accounts = data?.items ?? []
  const linkedProviders = useMemo(() => new Set(accounts.map((account) => account.provider)), [accounts])

  if (isLoading) {
    return <SkeletonCard />
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Connected accounts</CardTitle>
          <CardDescription>We could not load your connected accounts.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const handleLink = async (provider: "google" | "github") => {
    try {
      const redirectUrl = `${window.location.origin}/profile`
      const result = await startLink.mutateAsync({ provider, redirectUrl })
      if (result?.authorization_url) {
        window.location.href = result.authorization_url
        return
      }
      toast.error("Unable to start OAuth flow")
    } catch (error) {
      toast.error("Unable to start OAuth flow", {
        description: error instanceof Error ? error.message : "Try again later",
      })
    }
  }

  const handleUnlink = async (provider: string) => {
    try {
      await unlink.mutateAsync(provider)
      toast.success(`Unlinked ${provider}`)
    } catch (error) {
      toast.error("Unable to unlink account", {
        description: error instanceof Error ? error.message : "Try again later",
      })
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connected accounts</CardTitle>
        <CardDescription>Manage your linked OAuth providers.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {accounts.length === 0 && (
          <p className="text-muted-foreground text-sm">No connected accounts yet.</p>
        )}
        <div className="space-y-3">
          {accounts.map((account) => {
            const Icon = account.provider === "google" ? Icons.google : Icons.gitHub
            return (
              <div key={account.provider} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
                <div className="flex items-center gap-3">
                  <Icon className="h-4 w-4" />
                  <div>
                    <p className="font-medium capitalize">{account.provider}</p>
                    <p className="text-muted-foreground text-sm">{account.email}</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={() => handleUnlink(account.provider)}>
                  Unlink
                </Button>
              </div>
            )
          })}
        </div>
        <div className="flex flex-wrap gap-2">
          {oauthConfig?.googleEnabled && !linkedProviders.has("google") && (
            <OAuthLinkButton provider="google" onClick={() => handleLink("google")} disabled={startLink.isPending} />
          )}
          {oauthConfig?.githubEnabled && !linkedProviders.has("github") && (
            <OAuthLinkButton provider="github" onClick={() => handleLink("github")} disabled={startLink.isPending} />
          )}
        </div>
      </CardContent>
    </Card>
  )
}
