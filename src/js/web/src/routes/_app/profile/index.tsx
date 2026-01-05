import { createFileRoute } from "@tanstack/react-router"
import { ConnectedAccounts } from "@/components/profile/connected-accounts"
import { MfaSection } from "@/components/profile/mfa-section"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/profile/")({
  component: ProfilePage,
})

function ProfilePage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Account"
        title="Profile settings"
        description="Manage security, connected accounts, and authentication options."
      />
      <PageSection>
        <div className="grid gap-6 lg:grid-cols-2">
          <MfaSection />
          <ConnectedAccounts />
        </div>
      </PageSection>
    </PageContainer>
  )
}
