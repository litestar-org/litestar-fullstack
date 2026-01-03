import { createFileRoute } from "@tanstack/react-router"
import { ConnectedAccounts } from "@/components/profile/connected-accounts"
import { MfaSection } from "@/components/profile/mfa-section"

export const Route = createFileRoute("/_app/profile/")({
  component: ProfilePage,
})

function ProfilePage() {
  return (
    <div className="container mx-auto space-y-6 py-8">
      <div>
        <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Account</p>
        <h1 className="font-['Space_Grotesk'] text-3xl font-semibold">Profile settings</h1>
        <p className="text-muted-foreground">Manage security, connected accounts, and authentication options.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <MfaSection />
        <ConnectedAccounts />
      </div>
    </div>
  )
}
