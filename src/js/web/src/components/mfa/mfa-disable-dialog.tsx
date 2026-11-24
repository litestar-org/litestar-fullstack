import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useStepUpGrant } from "@/lib/api/hooks/auth"
import { useAuthStore } from "@/lib/auth"
import { mfaRemoveTotpMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

interface MfaDisableDialogProps {
  disabled?: boolean
  methodId?: string
}

export function MfaDisableDialog({ disabled, methodId = "totp" }: MfaDisableDialogProps) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState("")
  const user = useAuthStore((state) => state.user)
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const { requestGrant, isPending: stepUpPending } = useStepUpGrant()
  const removeTotp = useMutation(mfaRemoveTotpMutation())

  const hasPassword = user?.hasPassword ?? true
  const oauthProvider = user?.oauthAccounts?.[0]?.oauthName
  const isPending = stepUpPending || removeTotp.isPending

  const handlePasswordDisable = async () => {
    if (!password) {
      toast.error("Enter your password to disable MFA")
      return
    }
    try {
      const grant = await requestGrant("mfa-remove", password)
      await removeTotp.mutateAsync({
        path: { method_id: methodId },
        body: { step_up_grant: grant },
      })
      await checkAuth()
      toast.success("MFA disabled")
      setOpen(false)
      setPassword("")
    } catch (error) {
      toast.error("Unable to disable MFA", {
        description: error instanceof Error ? error.message : "Check your password and try again",
      })
    }
  }

  const handleOAuthDisable = () => {
    if (!oauthProvider) {
      toast.error("No linked OAuth account found")
      return
    }
    window.location.assign(`/api/auth/oauth/${encodeURIComponent(oauthProvider)}/login?return_to=${encodeURIComponent("/settings/security")}`)
  }

  const formatProviderName = (provider: string) => provider.charAt(0).toUpperCase() + provider.slice(1)

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
          <DialogDescription>{hasPassword ? "Confirm your password to turn off MFA." : "Re-authenticate with your linked account to turn off MFA."}</DialogDescription>
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
            <Button onClick={handleOAuthDisable} disabled={isPending}>
              Verify with {oauthProvider ? formatProviderName(oauthProvider) : "OAuth"}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
