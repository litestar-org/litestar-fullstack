import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useEffect } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { ConnectedAccounts } from "@/components/profile/connected-accounts"
import { MfaSection } from "@/components/profile/mfa-section"
import { PageContainer, PageHeader, PageSection } from "@/components/ui/page-layout"
import { profileOAuthAccountsQueryKey } from "@/lib/generated/api/@tanstack/react-query.gen"

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
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_app/profile/" })

  useEffect(() => {
    // Handle successful OAuth link
    if (searchParams.linked === "true" && searchParams.provider) {
      queryClient.invalidateQueries({ queryKey: profileOAuthAccountsQueryKey() })
      const providerName = searchParams.provider.charAt(0).toUpperCase() + searchParams.provider.slice(1)
      toast.success(`Successfully linked ${providerName} account`)
      void navigate({ to: "/profile", replace: true })
      return
    }
    // Handle OAuth error
    if (searchParams.oauth_failed) {
      toast.error(searchParams.message || "Failed to link account")
      void navigate({ to: "/profile", replace: true })
    }
  }, [searchParams, queryClient, navigate])

  return (
    <PageContainer className="flex-1 space-y-8">
      <PageHeader eyebrow="Account" title="Profile settings" description="Manage security, connected accounts, and authentication options." />
      <PageSection>
        <div className="grid gap-6 lg:grid-cols-2">
          <MfaSection />
          <ConnectedAccounts />
        </div>
      </PageSection>
    </PageContainer>
  )
}
