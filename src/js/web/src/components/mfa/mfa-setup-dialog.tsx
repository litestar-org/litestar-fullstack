import { useMutation } from "@tanstack/react-query"
import { QRCodeSVG } from "qrcode.react"
import { useState } from "react"
import { toast } from "sonner"
import { BackupCodesDisplay } from "@/components/mfa/backup-codes-display"
import { TOTP_CODE_LENGTH, TotpInput } from "@/components/mfa/totp-input"
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

const DEFAULT_DEVICE_LABEL = "Authenticator"

function extractManualSecret(provisioningUri: string): string | null {
  try {
    return new URL(provisioningUri).searchParams.get("secret")
  } catch {
    return null
  }
}

const STEP_DESCRIPTIONS = {
  password: "Confirm your current password to generate a new authenticator QR code.",
  verify: "Scan the QR code with your authenticator app, then enter the 6-digit verification code.",
  codes: "Save your recovery codes in a secure location.",
} as const

type SetupStep = keyof typeof STEP_DESCRIPTIONS

function resolveStep(provisioning: TotpProvisioning | null, recoveryCodes: string[] | null): SetupStep {
  if (recoveryCodes) {
    return "codes"
  }
  return provisioning ? "verify" : "password"
}

export function MfaSetupDialog({ disabled, onEnrolled }: Readonly<MfaSetupDialogProps>) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState("")
  const [deviceLabel, setDeviceLabel] = useState(DEFAULT_DEVICE_LABEL)
  const [provisioning, setProvisioning] = useState<TotpProvisioning | null>(null)
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null)
  const [totpCode, setTotpCode] = useState("")

  const { requestGrant, isPending: isStepUpPending } = useStepUpGrant()
  const enroll = useMutation(mfaEnrollTotpMutation())
  const verify = useMutation(mfaVerifyTotpEnrollmentMutation())
  const checkAuth = useAuthStore((state) => state.checkAuth)

  const isBusy = isStepUpPending || enroll.isPending || verify.isPending
  const isTotpCodeComplete = totpCode.length >= TOTP_CODE_LENGTH
  const manualSecret = provisioning ? extractManualSecret(provisioning.provisioning_uri) : null
  const step = resolveStep(provisioning, recoveryCodes)

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen)
    if (!nextOpen) {
      setPassword("")
      setDeviceLabel(DEFAULT_DEVICE_LABEL)
      setProvisioning(null)
      setRecoveryCodes(null)
      setTotpCode("")
    }
  }

  const handleStartSetup = async () => {
    if (!password) {
      toast.error("Confirm your password to begin MFA enrollment")
      return
    }
    try {
      const grant = await requestGrant("totp-enroll", password)
      const totpProvisioning = await enroll.mutateAsync({
        body: {
          label: deviceLabel.trim() || DEFAULT_DEVICE_LABEL,
          step_up_grant: grant,
        },
      })
      setProvisioning(totpProvisioning)
      setPassword("")
    } catch (error) {
      toast.error("Unable to start MFA setup", {
        description: extractApiErrorMessage(error, "Check your password and try again"),
      })
    }
  }

  const handleVerify = async () => {
    if (!provisioning || !isTotpCodeComplete) {
      toast.error("Enter the 6-digit code from your authenticator app")
      return
    }
    try {
      const { codes } = await verify.mutateAsync({
        body: {
          enrollment_id: provisioning.enrollment_id,
          code: totpCode,
        },
      })
      setRecoveryCodes(codes ?? [])
      onEnrolled?.(provisioning.method_id)
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
          <DialogDescription>{STEP_DESCRIPTIONS[step]}</DialogDescription>
        </DialogHeader>

        {recoveryCodes && (
          <BackupCodesDisplay codes={recoveryCodes} description="Save these codes in a secure place. Each code can be used once if you lose access to your authenticator." />
        )}
        {step === "verify" && provisioning && (
          <div className="space-y-4">
            <div className="flex justify-center rounded-lg border border-border/60 bg-white p-4">
              <QRCodeSVG value={provisioning.provisioning_uri} size={192} />
            </div>
            {manualSecret && <div className="rounded-lg border border-border/60 bg-muted/30 px-4 py-3 font-mono text-sm">{manualSecret}</div>}
            <TotpInput value={totpCode} onChange={setTotpCode} disabled={isBusy} autoFocus />
          </div>
        )}
        {step === "password" && (
          <div className="space-y-3">
            <Input placeholder="Device label (e.g. Authenticator)" value={deviceLabel} onChange={(event) => setDeviceLabel(event.target.value)} disabled={isBusy} />
            <Input type="password" placeholder="Current password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isBusy} />
          </div>
        )}

        <DialogFooter>
          {step === "codes" && <Button onClick={() => handleOpenChange(false)}>Done</Button>}
          {step === "verify" && (
            <Button onClick={handleVerify} disabled={isBusy || !isTotpCodeComplete}>
              Verify &amp; finish
            </Button>
          )}
          {step === "password" && (
            <Button onClick={handleStartSetup} disabled={isBusy || !password}>
              Continue
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
