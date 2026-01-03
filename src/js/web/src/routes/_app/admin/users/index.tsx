import { createFileRoute } from "@tanstack/react-router"
import { UserTable } from "@/components/admin/user-table"

export const Route = createFileRoute("/_app/admin/users/")({
  component: AdminUsersPage,
})

function AdminUsersPage() {
  return <UserTable />
}
