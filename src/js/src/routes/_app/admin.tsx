import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { User } from "@/lib/generated/api"
import { listUsers, updateUser } from "@/lib/generated/api/sdk.gen"
import { useAuthStore } from "@/lib/auth"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/_app/admin")({
  component: Admin,
})

function Admin() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const response = await listUsers()
      return response.data?.items ?? []
    },
  })

  const toggleSuperuserMutation = useMutation({
    mutationFn: (userId: string) =>
      updateUser({
        path: { user_id: userId },
        body: { isSuperuser: true },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const handleToggleSuperuser = async (userId: string) => {
    try {
      await toggleSuperuserMutation.mutateAsync(userId)
    } catch (error) {
      console.error("Failed to toggle superuser status:", error)
    }
  }

  if (!user?.isSuperuser) {
    navigate({ to: "/home" as const })
    return null
  }

  if (isLoading) {
    return <div className="text-muted-foreground">Loading users…</div>
  }

  return (
    <div className="container mx-auto space-y-6 py-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Administration</p>
          <h1 className="font-['Space_Grotesk'] text-3xl font-semibold">User management</h1>
          <p className="text-muted-foreground">Promote admins, audit access, and keep the directory tidy.</p>
        </div>
      </div>

      <Card className="border-border/60 bg-card/80 shadow-lg shadow-primary/10">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Directory</CardTitle>
          <Badge variant="outline">{users.length} users</Badge>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((row: User) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium">{row.name}</TableCell>
                  <TableCell className="text-muted-foreground">{row.email}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {row.isSuperuser ? <Badge variant="secondary">Superuser</Badge> : <Badge variant="outline">Member</Badge>}
                      <Button variant="outline" size="sm" onClick={() => handleToggleSuperuser(row.id)}>
                        {row.isSuperuser ? "Remove admin" : "Make admin"}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

export default Admin
