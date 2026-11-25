import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"
import { BackupCodesDisplay } from "@/components/mfa/backup-codes-display"
import { MfaDisableDialog } from "@/components/mfa/mfa-disable-dialog"
import { MfaSetupDialog } from "@/components/mfa/mfa-setup-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useAuthConfig, useStepUpGrant } from "@/lib/api/hooks/auth"
import { extractApiErrorMessage } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import { mfaReplaceRecoveryCodesMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export function MfaSection() {
  const user = useAuthStore((state) => state.user)
  const { data: authConfig } = useAuthConfig()
  const [enrolledMethodId, setEnrolledMethodId] = useState<string | null>(null)
  const [isRegenerateDialogOpen, setIsRegenerateDialogOpen] = useState(false)

  if (authConfig?.mfaEnabled === false) {
    return null
  }

  const isMfaEnabled = user?.isTwoFactorEnabled ?? false
  const activeMethodId = user?.totpMethodId ?? enrolledMethodId

  return (
    <Card>
      <CardHeader>
        <CardTitle>Multi-factor authentication</CardTitle>
        <CardDescription>{isMfaEnabled ? "MFA is enabled on your account." : "Add an extra layer of security to your account."}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isMfaEnabled ? (
          <div className="flex flex-wrap gap-2">
            <MfaDisableDialog methodId={activeMethodId} />
            <Button variant="outline" onClick={() => setIsRegenerateDialogOpen(true)}>
              Regenerate recovery codes
            </Button>
          </div>
        ) : (
          <MfaSetupDialog onEnrolled={setEnrolledMethodId} />
        )}
      </CardContent>
      <RegenerateRecoveryCodesDialog open={isRegenerateDialogOpen} onOpenChange={setIsRegenerateDialogOpen} />
    </Card>
  )
}

interface RegenerateRecoveryCodesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function RegenerateRecoveryCodesDialog({ open, onOpenChange }: Readonly<RegenerateRecoveryCodesDialogProps>) {
  const { requestGrant, isPending: isStepUpPending } = useStepUpGrant()
  const replaceRecoveryCodes = useMutation(mfaReplaceRecoveryCodesMutation())
  const [password, setPassword] = useState("")
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null)

  const isRegenerating = isStepUpPending || replaceRecoveryCodes.isPending

  const handleOpenChange = (nextOpen: boolean) => {
    onOpenChange(nextOpen)
    if (!nextOpen) {
      setPassword("")
      setRecoveryCodes(null)
    }
  }

  const handleRegenerate = async () => {
    if (!password) {
      toast.error("Enter your password to regenerate backup codes")
      return
    }
    try {
      const grant = await requestGrant("recovery-codes", password)
      const { codes } = await replaceRecoveryCodes.mutateAsync({ body: { step_up_grant: grant } })
      setRecoveryCodes(codes ?? [])
      setPassword("")
      toast.success("Recovery codes regenerated")
    } catch (error) {
      toast.error("Unable to regenerate codes", {
        description: extractApiErrorMessage(error, "Try again later"),
      })
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Regenerate recovery codes</DialogTitle>
          <DialogDescription>Confirm your password to generate a fresh set of one-time recovery codes.</DialogDescription>
        </DialogHeader>
        {recoveryCodes ? (
          <BackupCodesDisplay codes={recoveryCodes} description="These codes replace your previous set. Store them securely." />
        ) : (
          <Input type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isRegenerating} />
        )}
        <DialogFooter>
          {recoveryCodes ? (
            <Button onClick={() => handleOpenChange(false)}>Done</Button>
          ) : (
            <Button onClick={handleRegenerate} disabled={isRegenerating}>
              Regenerate
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
