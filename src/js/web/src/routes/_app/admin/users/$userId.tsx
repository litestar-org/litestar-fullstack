import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"
import { AdminNav } from "@/components/admin/admin-nav"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { SkeletonCard } from "@/components/ui/skeleton"
import { useAdminUpdateUser, useAdminUser } from "@/lib/api/hooks/admin"

export const Route = createFileRoute("/_app/admin/users/$userId")({
  component: AdminUserDetailPage,
})

function AdminUserDetailPage() {
  const { userId } = Route.useParams()
  const { data, isLoading, isError } = useAdminUser(userId)
  const updateUser = useAdminUpdateUser(userId)

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
              <Button variant="outline" onClick={() => updateUser.mutate({ is_active: !data.isActive })} disabled={updateUser.isPending}>
                {data.isActive ? "Deactivate" : "Activate"}
              </Button>
              <Button variant="outline" onClick={() => updateUser.mutate({ is_superuser: !data.isSuperuser })} disabled={updateUser.isPending}>
                {data.isSuperuser ? "Remove superuser" : "Make superuser"}
              </Button>
              <Button variant="outline" onClick={() => updateUser.mutate({ is_verified: !data.isVerified })} disabled={updateUser.isPending}>
                {data.isVerified ? "Mark unverified" : "Mark verified"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </PageSection>
    </PageContainer>
  )
}
