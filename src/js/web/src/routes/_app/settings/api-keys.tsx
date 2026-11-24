import { createFileRoute } from "@tanstack/react-router"
import { ApiKeysSection } from "@/components/settings/api-keys-section"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/settings/api-keys")({
  component: ApiKeysSettingsPage,
})

function ApiKeysSettingsPage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader eyebrow="Settings" title="API Keys" description="Issue, rotate, and revoke personal API keys for MCP and CLI automation." />
      <PageSection>
        <ApiKeysSection />
      </PageSection>
    </PageContainer>
  )
}
