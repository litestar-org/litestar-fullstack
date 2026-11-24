import { browserSupportsWebAuthn } from "@simplewebauthn/browser"
import { useNavigate } from "@tanstack/react-router"
import { KeyRound } from "lucide-react"
import { toast } from "sonner"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/lib/auth"
import { DEFAULT_AUTH_REDIRECT } from "@/lib/redirect-utils"

interface PasskeySignInButtonProps {
  accountId?: string
  authRedirect?: string
  className?: string
}

export function PasskeySignInButton({ accountId, authRedirect, className }: PasskeySignInButtonProps) {
  const navigate = useNavigate()
  const loginWithPasskey = useAuthStore((state) => state.loginWithPasskey)
  const storedAccountId = useAuthStore((state) => state.passkeyAccountId)
  const isLoading = useAuthStore((state) => state.isLoading)

  if (!browserSupportsWebAuthn()) {
    return null
  }

  const effectiveAccountId = accountId?.trim() || storedAccountId || undefined
  const isDisabled = isLoading || !effectiveAccountId

  const handleClick = async () => {
    if (!effectiveAccountId) {
      return
    }
    const ok = await loginWithPasskey(effectiveAccountId)
    if (ok) {
      toast.success("Signed in with passkey")
      navigate({ to: authRedirect || DEFAULT_AUTH_REDIRECT })
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      onClick={handleClick}
      disabled={isDisabled}
      title={effectiveAccountId ? undefined : "Sign in once on this device to enable passkey sign-in"}
      className={className}
    >
      {isLoading ? <Icons.spinner className="mr-2 h-4 w-4 animate-spin" /> : <KeyRound className="mr-2 h-4 w-4" />}
      Sign in with Passkey
    </Button>
  )
}
