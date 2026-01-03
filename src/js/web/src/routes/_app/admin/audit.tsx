import { createFileRoute } from "@tanstack/react-router"
import { AuditLogTable } from "@/components/admin/audit-log-table"

export const Route = createFileRoute("/_app/admin/audit")({
  component: AdminAuditPage,
})

function AdminAuditPage() {
  return <AuditLogTable />
}
