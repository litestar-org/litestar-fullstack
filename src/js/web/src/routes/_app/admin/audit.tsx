import { createFileRoute } from "@tanstack/react-router"
import { AdminNav } from "@/components/admin/admin-nav"
import { AuditLogTable } from "@/components/admin/audit-log-table"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"

export const Route = createFileRoute("/_app/admin/audit")({
  component: AdminAuditPage,
})

function AdminAuditPage() {
  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader eyebrow="Administration" title="Audit Log" description="Track system events and user actions." />
      <AdminNav />
      <PageSection>
        <AuditLogTable />
      </PageSection>
    </PageContainer>
  )
}
