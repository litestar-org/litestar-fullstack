import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { assignUserRole, listUsers, revokeUserRole, type User } from "@/lib/generated/api"
import { useQuery } from "@tanstack/react-query"

export function AdminUsers() {
  const {
    data: users = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const response = await listUsers()
      return response.data?.items ?? []
    },
  })

  if (isLoading) {
    return <div className="text-muted-foreground">Loading users…</div>
  }

  if (isError) {
    return <div className="text-muted-foreground">We couldn’t load users yet. Try again shortly.</div>
  }

  const handleToggleSuperuser = async (user: User) => {
    try {
      const isSuperuser = user.roles?.some((role) => role.roleSlug === "superuser")
      if (isSuperuser) {
        await revokeUserRole({
          body: { userName: user.email },
          query: { role_slug: "superuser" },
        })
      } else {
        await assignUserRole({
          body: { userName: user.email },
          query: { role_slug: "superuser" },
        })
      }
      refetch()
    } catch (error) {
      console.error("Failed to toggle superuser status:", error)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Users</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
        <TableBody>
          {users.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No users available yet.
              </TableCell>
            </TableRow>
          )}
          {users.map((user: User) => (
            <TableRow key={user.id}>
              <TableCell>{user.name ?? user.email}</TableCell>
              <TableCell className="text-muted-foreground">{user.email}</TableCell>
              <TableCell>{user.roles?.map((role) => role.roleName).join(", ") || "Member"}</TableCell>
              <TableCell>
                <Button variant="outline" size="sm" onClick={() => handleToggleSuperuser(user)}>
                  Toggle Superuser
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
