import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { toast } from "sonner"
import { TotpInput } from "@/components/mfa/totp-input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useVerifyMfaChallenge } from "@/lib/api/hooks/auth"
import { useAuthStore } from "@/lib/auth"

export const Route = createFileRoute("/_public/mfa-challenge")({
  component: MfaChallengePage,
})

function MfaChallengePage() {
  const navigate = useNavigate()
  const { completeMfaLogin } = useAuthStore()
  const verify = useVerifyMfaChallenge()
  const [tab, setTab] = useState("totp")
  const [code, setCode] = useState("")
  const [recoveryCode, setRecoveryCode] = useState("")

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
      navigate({ to: "/home" })
    } catch (error) {
      toast.error("Verification failed", {
        description: error instanceof Error ? error.message : "Try again",
      })
    }
  }

  const disableAction = verify.isPending || (tab === "totp" ? code.length < 6 : !recoveryCode)

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Verify your identity</CardTitle>
          <CardDescription>Enter a code from your authenticator app or a backup code.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="totp">Authenticator</TabsTrigger>
              <TabsTrigger value="recovery">Backup code</TabsTrigger>
            </TabsList>
            <TabsContent value="totp" className="space-y-3">
              <TotpInput value={code} onChange={setCode} autoFocus />
            </TabsContent>
            <TabsContent value="recovery" className="space-y-3">
              <Input placeholder="XXXX-XXXX" value={recoveryCode} onChange={(event) => setRecoveryCode(event.target.value)} />
            </TabsContent>
          </Tabs>
          <Button className="w-full" onClick={handleVerify} disabled={disableAction}>
            Verify
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
