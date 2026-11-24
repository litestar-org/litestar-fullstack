import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"
import { AdminNav } from "@/components/admin/admin-nav"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { SkeletonCard } from "@/components/ui/skeleton"
import { extractApiErrorMessage } from "@/lib/api-client"
import { adminGetUserOptions, adminGetUserQueryKey, adminListUsersQueryKey, adminUpdateUserMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export const Route = createFileRoute("/_app/admin/users/$userId")({
  component: AdminUserDetailPage,
})

function AdminUserDetailPage() {
  const { userId } = Route.useParams()
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    ...adminGetUserOptions({ path: { user_id: userId } }),
    enabled: Boolean(userId),
  })
  const updateUser = useMutation({
    ...adminUpdateUserMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminListUsersQueryKey() })
      queryClient.invalidateQueries({ queryKey: adminGetUserQueryKey({ path: { user_id: userId } }) })
      toast.success("User updated")
    },
    onError: (error) => {
      toast.error("Unable to update user", {
        description: extractApiErrorMessage(error, "Try again later"),
      })
    },
  })

  if (isLoading) {
    return (
      <PageContainer className="flex-1 space-y-8">
        <PageHeader eyebrow="Administration" title="User Details" />
        <AdminNav />
        <PageSection>
          <SkeletonCard />
        </PageSection>
      </PageContainer>
    )
  }

  if (isError || !data) {
    return (
      <PageContainer className="flex-1 space-y-8">
        <PageHeader
          eyebrow="Administration"
          title="User Details"
          actions={
            <Button variant="outline" size="sm" asChild>
              <Link to="/admin/users">
                <ArrowLeft className="mr-2 h-4 w-4" /> Back to users
              </Link>
            </Button>
          }
        />
        <AdminNav />
        <PageSection>
          <Card>
            <CardHeader>
              <CardTitle>User detail</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">We could not load this user.</CardContent>
          </Card>
        </PageSection>
      </PageContainer>
    )
  }

  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Administration"
        title={data.name ?? data.email}
        description="Manage user account settings and permissions."
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link to="/admin/users">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to users
            </Link>
          </Button>
        }
      />
      <AdminNav />
      <PageSection>
        <Card>
          <CardContent className="space-y-4">
            <div className="grid gap-3 text-sm md:grid-cols-2">
              <div>
                <p className="text-muted-foreground">Email</p>
                <p>{data.email}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Username</p>
                <p>{data.username ?? "—"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p>{data.isActive ? "Active" : "Inactive"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Superuser</p>
                <p>{data.isSuperuser ? "Yes" : "No"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Verified</p>
                <p>{data.isVerified ? "Yes" : "No"}</p>
              </div>
              <div>
                <p className="text-muted-foreground">MFA enabled</p>
                <p>{data.isTwoFactorEnabled ? "Yes" : "No"}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => updateUser.mutate({ path: { user_id: userId }, body: { isActive: !data.isActive } })} disabled={updateUser.isPending}>
                {data.isActive ? "Deactivate" : "Activate"}
              </Button>
              <Button variant="outline" onClick={() => updateUser.mutate({ path: { user_id: userId }, body: { isSuperuser: !data.isSuperuser } })} disabled={updateUser.isPending}>
                {data.isSuperuser ? "Remove superuser" : "Make superuser"}
              </Button>
              <Button variant="outline" onClick={() => updateUser.mutate({ path: { user_id: userId }, body: { isVerified: !data.isVerified } })} disabled={updateUser.isPending}>
                {data.isVerified ? "Mark unverified" : "Mark verified"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </PageSection>
    </PageContainer>
  )
}
