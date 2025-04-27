import { createFileRoute } from '@tanstack/react-router'
import { useAuthStore } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { useState, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const Route = createFileRoute('/_app/admin')({
  component: AdminComponent,
})

function AdminComponent() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const response = await api.admin.users.list();
      return response.data;
    },
  });

  const toggleSuperuserMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await api.admin.users.toggleSuperuser({
        params: { userId },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  if (!user?.is_superuser) {
    navigate({ to: '/_app/home' })
    return null;
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      </div>

      <div className="rounded-lg border">
        <div className="p-4">
          <h2 className="text-lg font-semibold">Users</h2>
        </div>
        <div className="divide-y">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Superuser</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>{user.is_superuser ? "Yes" : "No"}</td>
                  <td>
                    <Button
                      variant={user.is_superuser ? 'default' : 'outline'}
                      onClick={() => toggleSuperuserMutation.mutate(user.id)}
                    >
                      {user.is_superuser ? 'Remove Superuser' : 'Make Superuser'}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AdminComponent;
