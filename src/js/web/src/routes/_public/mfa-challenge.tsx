import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { AuthHeroPanel } from "@/components/auth/auth-hero-panel"
import { TotpInput } from "@/components/mfa/totp-input"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useVerifyMfaChallenge } from "@/lib/api/hooks/auth"
import { useAuthStore } from "@/lib/auth"
import { getSafeRedirectUrl } from "@/lib/redirect-utils"

export const Route = createFileRoute("/_public/mfa-challenge")({
  validateSearch: (search) =>
    z
      .object({
        redirect: z.string().optional(),
      })
      .parse(search),
  component: MfaChallengePage,
})

function MfaChallengePage() {
  const navigate = useNavigate()
  const { redirect } = useSearch({ from: "/_public/mfa-challenge" })
  const { completeMfaLogin } = useAuthStore()
  const verify = useVerifyMfaChallenge()
  const [tab, setTab] = useState("totp")
  const [code, setCode] = useState("")
  const [recoveryCode, setRecoveryCode] = useState("")

  // Validate and get safe redirect destination
  const finalRedirect = getSafeRedirectUrl(redirect)

  const handleVerify = async () => {
    try {
      const payload = tab === "totp" ? { code } : { recovery_code: recoveryCode.trim().toUpperCase() }
      const response = await verify.mutateAsync(payload)
      const accessToken = (response as { access_token?: string })?.access_token
      if (!accessToken) {
        toast.error("Verification failed")
        return
      }
      await completeMfaLogin(accessToken)
      toast.success("MFA verified")
      navigate({ to: finalRedirect })
    } catch (error) {
      toast.error("Verification failed", {
        description: error instanceof Error ? error.message : "Try again",
      })
    }
  }

  const disableAction = verify.isPending || (tab === "totp" ? code.length < 6 : !recoveryCode)

  return (
    <div className="relative flex min-h-screen w-full">
      <AuthHeroPanel showTestimonial={false} description="Two-factor authentication keeps your account secure." />
      <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-semibold tracking-tight">Verify your identity</h1>
            <p className="mt-2 text-sm text-muted-foreground">Enter a code from your authenticator app or a backup code.</p>
          </div>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="totp">Authenticator</TabsTrigger>
              <TabsTrigger value="recovery">Backup code</TabsTrigger>
            </TabsList>
            <TabsContent value="totp" className="space-y-3 pt-4">
              <TotpInput value={code} onChange={setCode} autoFocus />
            </TabsContent>
            <TabsContent value="recovery" className="space-y-3 pt-4">
              <Input placeholder="XXXX-XXXX" value={recoveryCode} onChange={(event) => setRecoveryCode(event.target.value)} />
            </TabsContent>
          </Tabs>

          <Button className="w-full" onClick={handleVerify} disabled={disableAction}>
            Verify
          </Button>
        </div>
      </div>
    </div>
  )
}
