import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { User } from "@/lib/api"
import { assignUserRole, listUsers, revokeUserRole } from "@/lib/api/sdk.gen"
import { useQuery } from "@tanstack/react-query"

export function AdminUsers() {
  const {
    data: users = [],
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const response = await listUsers()
      return response.data?.items ?? []
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  const handleToggleSuperuser = async (user: User) => {
    try {
      const isSuperuser = user.roles?.some((role) => role.roleSlug === "superuser")
      if (isSuperuser) {
        await revokeUserRole({
          body: { userName: user.name || user.email },
          query: { role_slug: "superuser" },
        })
      } else {
        await assignUserRole({
          body: { userName: user.name || user.email },
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
            {users.map((user: User) => (
              <TableRow key={user.id}>
                <TableCell>{user.name}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.roles?.map((role) => role.roleName).join(", ")}</TableCell>
                <TableCell>
                  <Button variant="destructive" size="sm" onClick={() => handleToggleSuperuser(user)}>
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
