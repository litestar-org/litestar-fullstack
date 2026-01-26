import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useDisableMfa, useInitiateDisableMfaOAuth } from "@/lib/api/hooks/auth"
import { useAuthStore } from "@/lib/auth"

interface MfaDisableDialogProps {
  disabled?: boolean
}

export function MfaDisableDialog({ disabled }: MfaDisableDialogProps) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState("")
  const { user } = useAuthStore()
  const disableMfa = useDisableMfa()
  const initiateOAuth = useInitiateDisableMfaOAuth()

  const hasPassword = user?.hasPassword ?? true
  const oauthProvider = user?.oauthAccounts?.[0]?.oauthName

  const handlePasswordDisable = async () => {
    if (!password) {
      toast.error("Enter your password to disable MFA")
      return
    }
    try {
      await disableMfa.mutateAsync(password)
      setOpen(false)
      setPassword("")
    } catch (error) {
      toast.error("Unable to disable MFA", {
        description: error instanceof Error ? error.message : "Check your password and try again",
      })
    }
  }

  const handleOAuthDisable = async () => {
    if (!oauthProvider) {
      toast.error("No linked OAuth account found")
      return
    }
    try {
      const result = await initiateOAuth.mutateAsync(oauthProvider)
      if (result.authorizationUrl) {
        window.location.href = result.authorizationUrl
      }
    } catch (error) {
      toast.error("Unable to start OAuth verification", {
        description: error instanceof Error ? error.message : "Please try again",
      })
    }
  }

  const formatProviderName = (provider: string) => {
    return provider.charAt(0).toUpperCase() + provider.slice(1)
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
          <DialogDescription>{hasPassword ? "Confirm your password to turn off MFA." : "Re-authenticate with your linked account to turn off MFA."}</DialogDescription>
        </DialogHeader>

        {hasPassword ? (
          <>
            <Input type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} />
            <DialogFooter>
              <Button onClick={handlePasswordDisable} disabled={disableMfa.isPending}>
                Disable MFA
              </Button>
            </DialogFooter>
          </>
        ) : (
          <DialogFooter>
            <Button onClick={handleOAuthDisable} disabled={initiateOAuth.isPending}>
              Verify with {oauthProvider ? formatProviderName(oauthProvider) : "OAuth"}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
