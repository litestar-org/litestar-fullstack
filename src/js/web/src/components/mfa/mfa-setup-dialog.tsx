import { useMutation } from "@tanstack/react-query"
import { QRCodeSVG } from "qrcode.react"
import { useMemo, useState } from "react"
import { toast } from "sonner"
import { BackupCodesDisplay } from "@/components/mfa/backup-codes-display"
import { TotpInput } from "@/components/mfa/totp-input"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useStepUpGrant } from "@/lib/api/hooks/auth"
import { extractApiErrorMessage } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import type { TotpProvisioning } from "@/lib/generated/api"
import { mfaEnrollTotpMutation, mfaVerifyTotpEnrollmentMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

interface MfaSetupDialogProps {
  disabled?: boolean
  onEnrolled?: (methodId: string) => void
}

function extractManualSecret(provisioningUri: string): string | null {
  try {
    return new URL(provisioningUri).searchParams.get("secret")
  } catch {
    return null
  }
}

export function MfaSetupDialog({ disabled, onEnrolled }: MfaSetupDialogProps) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState("")
  const [label, setLabel] = useState("Authenticator")
  const [setup, setSetup] = useState<TotpProvisioning | null>(null)
  const [codes, setCodes] = useState<string[] | null>(null)
  const [code, setCode] = useState("")

  const { requestGrant, isPending: stepUpPending } = useStepUpGrant()
  const enroll = useMutation(mfaEnrollTotpMutation())
  const verify = useMutation(mfaVerifyTotpEnrollmentMutation())
  const checkAuth = useAuthStore((state) => state.checkAuth)

  const isLoading = stepUpPending || enroll.isPending || verify.isPending
  const manualSecret = useMemo(() => (setup ? extractManualSecret(setup.provisioning_uri) : null), [setup])

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen)
    if (!nextOpen) {
      setPassword("")
      setLabel("Authenticator")
      setSetup(null)
      setCodes(null)
      setCode("")
    }
  }

  const handleStartSetup = async () => {
    if (!password) {
      toast.error("Confirm your password to begin MFA enrollment")
      return
    }
    try {
      const grant = await requestGrant("totp-enroll", password)
      const provisioned = await enroll.mutateAsync({
        body: {
          label: label.trim() || "Authenticator",
          step_up_grant: grant,
        },
      })
      setSetup(provisioned)
      setPassword("")
    } catch (error) {
      toast.error("Unable to start MFA setup", {
        description: extractApiErrorMessage(error, "Check your password and try again"),
      })
    }
  }

  const handleConfirm = async () => {
    if (!setup || code.length < 6) {
      toast.error("Enter the 6-digit code from your authenticator app")
      return
    }
    try {
      const result = await verify.mutateAsync({
        body: {
          enrollment_id: setup.enrollment_id,
          code,
        },
      })
      setCodes(result.codes ?? [])
      onEnrolled?.(setup.method_id)
      await checkAuth()
      toast.success("MFA enabled")
    } catch (error) {
      toast.error("Verification failed", {
        description: extractApiErrorMessage(error, "Check the code and try again"),
      })
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button disabled={disabled}>Enable MFA</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enable multi-factor authentication</DialogTitle>
          <DialogDescription>
            {codes
              ? "Save your recovery codes in a secure location."
              : setup
                ? "Scan the QR code with your authenticator app, then enter the 6-digit verification code."
                : "Confirm your current password to generate a new authenticator QR code."}
          </DialogDescription>
        </DialogHeader>

        {codes ? (
          <BackupCodesDisplay codes={codes} description="Save these codes in a secure place. Each code can be used once if you lose access to your authenticator." />
        ) : setup ? (
          <div className="space-y-4">
            <div className="flex justify-center rounded-lg border border-border/60 bg-white p-4">
              <QRCodeSVG value={setup.provisioning_uri} size={192} />
            </div>
            {manualSecret && <div className="rounded-lg border border-border/60 bg-muted/30 px-4 py-3 font-mono text-sm">{manualSecret}</div>}
            <TotpInput value={code} onChange={setCode} disabled={isLoading} autoFocus />
          </div>
        ) : (
          <div className="space-y-3">
            <Input placeholder="Device label (e.g. Authenticator)" value={label} onChange={(event) => setLabel(event.target.value)} disabled={isLoading} />
            <Input type="password" placeholder="Current password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isLoading} />
          </div>
        )}

        <DialogFooter>
          {codes ? (
            <Button onClick={() => handleOpenChange(false)}>Done</Button>
          ) : setup ? (
            <Button onClick={handleConfirm} disabled={isLoading || code.length < 6}>
              Verify &amp; finish
            </Button>
          ) : (
            <Button onClick={handleStartSetup} disabled={isLoading || !password}>
              Continue
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
