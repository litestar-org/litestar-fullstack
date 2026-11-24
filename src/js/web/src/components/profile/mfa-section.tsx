import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"
import { BackupCodesDisplay } from "@/components/mfa/backup-codes-display"
import { MfaDisableDialog } from "@/components/mfa/mfa-disable-dialog"
import { MfaSetupDialog } from "@/components/mfa/mfa-setup-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useStepUpGrant } from "@/lib/api/hooks/auth"
import { extractApiErrorMessage } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import { mfaReplaceRecoveryCodesMutation, publicAuthConfigOptions } from "@/lib/generated/api/@tanstack/react-query.gen"

export function MfaSection() {
  const user = useAuthStore((state) => state.user)
  const { data: authConfig } = useQuery({
    ...publicAuthConfigOptions(),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const { requestGrant, isPending: stepUpPending } = useStepUpGrant()
  const regenerate = useMutation(mfaReplaceRecoveryCodesMutation())
  const [enrolledMethodId, setEnrolledMethodId] = useState<string | null>(null)
  const [regenOpen, setRegenOpen] = useState(false)
  const [regenPassword, setRegenPassword] = useState("")
  const [regenCodes, setRegenCodes] = useState<string[] | null>(null)

  if (authConfig && authConfig.mfaEnabled === false) {
    return null
  }

  const mfaEnabled = user?.isTwoFactorEnabled ?? false
  const activeMethodId = user?.totpMethodId ?? enrolledMethodId
  const isRegenPending = stepUpPending || regenerate.isPending

  const handleRegenOpenChange = (nextOpen: boolean) => {
    setRegenOpen(nextOpen)
    if (!nextOpen) {
      setRegenPassword("")
      setRegenCodes(null)
    }
  }

  const handleRegenerate = async () => {
    if (!regenPassword) {
      toast.error("Enter your password to regenerate backup codes")
      return
    }
    try {
      const grant = await requestGrant("recovery-codes", regenPassword)
      const result = await regenerate.mutateAsync({ body: { step_up_grant: grant } })
      setRegenCodes(result.codes ?? [])
      setRegenPassword("")
      toast.success("Recovery codes regenerated")
    } catch (error) {
      toast.error("Unable to regenerate codes", {
        description: extractApiErrorMessage(error, "Try again later"),
      })
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Multi-factor authentication</CardTitle>
        <CardDescription>{mfaEnabled ? "MFA is enabled on your account." : "Add an extra layer of security to your account."}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {mfaEnabled ? (
          <div className="flex flex-wrap gap-2">
            <MfaDisableDialog methodId={activeMethodId} />
            <Button variant="outline" onClick={() => setRegenOpen(true)}>
              Regenerate recovery codes
            </Button>
          </div>
        ) : (
          <MfaSetupDialog onEnrolled={setEnrolledMethodId} />
        )}
      </CardContent>
      <Dialog open={regenOpen} onOpenChange={handleRegenOpenChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Regenerate recovery codes</DialogTitle>
            <DialogDescription>Confirm your password to generate a fresh set of one-time recovery codes.</DialogDescription>
          </DialogHeader>
          {regenCodes ? (
            <BackupCodesDisplay codes={regenCodes} description="These codes replace your previous set. Store them securely." />
          ) : (
            <Input type="password" placeholder="Password" value={regenPassword} onChange={(event) => setRegenPassword(event.target.value)} disabled={isRegenPending} />
          )}
          <DialogFooter>
            {regenCodes ? (
              <Button onClick={() => handleRegenOpenChange(false)}>Done</Button>
            ) : (
              <Button onClick={handleRegenerate} disabled={isRegenPending}>
                Regenerate
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
