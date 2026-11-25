import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Key, Shield } from "lucide-react"
import { useEffect } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { ConnectedAccounts } from "@/components/profile/connected-accounts"
import { MfaSection } from "@/components/profile/mfa-section"
import { Button } from "@/components/ui/button"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { useAuthStore } from "@/lib/auth"

const profileSearchSchema = z
  .object({
    provider: z.string().optional(),
    action: z.string().optional(),
    linked: z.coerce.string().optional(),
    oauth_failed: z.string().optional(),
    message: z.string().optional(),
  })
  .passthrough()

export const Route = createFileRoute("/_app/profile/")({
  validateSearch: (search) => profileSearchSchema.parse(search),
  component: ProfilePage,
})

function ProfilePage() {
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_app/profile/" })
  const checkAuth = useAuthStore((state) => state.checkAuth)

  useEffect(() => {
    if (searchParams.linked === "true" && searchParams.provider) {
      void checkAuth()
      const providerName = searchParams.provider.charAt(0).toUpperCase() + searchParams.provider.slice(1)
      toast.success(`Successfully linked ${providerName} account`)
      void navigate({ to: "/profile", replace: true })
      return
    }
    if (searchParams.oauth_failed) {
      toast.error(searchParams.message || "Failed to link account")
      void navigate({ to: "/profile", replace: true })
    }
  }, [searchParams, checkAuth, navigate])

  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader
        eyebrow="Account"
        title="Profile settings"
        description="Manage security, connected accounts, and authentication options."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline" size="sm">
              <Link to="/settings/security">
                <Shield className="mr-1.5 h-4 w-4" />
                Security &amp; Passkeys
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link to="/settings/api-keys">
                <Key className="mr-1.5 h-4 w-4" />
                API Keys
              </Link>
            </Button>
          </div>
        }
      />
      <PageSection>
        <div className="grid gap-6 lg:grid-cols-2">
          <MfaSection />
          <ConnectedAccounts />
        </div>
      </PageSection>
    </PageContainer>
  )
}
