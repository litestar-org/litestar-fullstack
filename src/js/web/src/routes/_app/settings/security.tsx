import { createFileRoute } from "@tanstack/react-router"
import { ConnectedAccounts } from "@/components/profile/connected-accounts"
import { MfaSection } from "@/components/profile/mfa-section"
import { PasskeysSection } from "@/components/settings/passkeys-section"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/settings/security")({
  component: SecuritySettingsPage,
})

function SecuritySettingsPage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader eyebrow="Settings" title="Security" description="Manage multi-factor authentication, passkeys, and linked OAuth providers." />
      <PageSection>
        <div className="grid gap-6 lg:grid-cols-2">
          <MfaSection />
          <PasskeysSection />
          <div className="lg:col-span-2">
            <ConnectedAccounts />
          </div>
        </div>
      </PageSection>
    </PageContainer>
  )
}
