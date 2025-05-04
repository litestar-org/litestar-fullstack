import { Button } from "@/components/ui/button"
import type { User } from "@/lib/api"
import { listUsers, updateUser } from "@/lib/api/sdk.gen"
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
    return <div>Loading...</div>
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <table className="min-w-full">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user: User) => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>
                <Button onClick={() => handleToggleSuperuser(user.id)}>Toggle Superuser</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Admin
