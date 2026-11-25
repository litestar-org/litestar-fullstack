import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useStepUpGrant } from "@/lib/api/hooks/auth"
import { extractApiErrorMessage } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import { mfaRemoveTotpMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

interface MfaDisableDialogProps {
  disabled?: boolean
  methodId?: string | null
}

export function MfaDisableDialog({ disabled, methodId }: Readonly<MfaDisableDialogProps>) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState("")
  const user = useAuthStore((state) => state.user)
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const { requestGrant, isPending: stepUpPending } = useStepUpGrant()
  const removeTotp = useMutation(mfaRemoveTotpMutation())

  const hasPassword = user?.hasPassword ?? true
  const resolvedMethodId = methodId ?? user?.totpMethodId ?? null
  const isPending = stepUpPending || removeTotp.isPending

  const handlePasswordDisable = async () => {
    if (!password) {
      toast.error("Enter your password to disable MFA")
      return
    }
    if (!resolvedMethodId) {
      toast.error("Unable to identify active MFA factor. Reload and try again.")
      return
    }
    try {
      const grant = await requestGrant("totp-remove", password)
      await removeTotp.mutateAsync({
        path: { method_id: resolvedMethodId },
        body: { step_up_grant: grant },
      })
      await checkAuth()
      toast.success("MFA disabled")
      setOpen(false)
      setPassword("")
    } catch (error) {
      toast.error("Unable to disable MFA", {
        description: extractApiErrorMessage(error, "Check your password and try again"),
      })
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" disabled={disabled}>
          Disable MFA
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disable multi-factor authentication</DialogTitle>
          <DialogDescription>
            {hasPassword
              ? "Confirm your password to turn off MFA."
              : "Disabling MFA requires password step-up verification. Set a password in your profile settings before disabling MFA."}
          </DialogDescription>
        </DialogHeader>

        {hasPassword ? (
          <>
            <Input type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isPending} />
            <DialogFooter>
              <Button onClick={handlePasswordDisable} disabled={isPending}>
                Disable MFA
              </Button>
            </DialogFooter>
          </>
        ) : (
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
