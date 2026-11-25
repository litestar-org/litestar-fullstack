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

export function PasskeySignInButton({ accountId, authRedirect, className }: Readonly<PasskeySignInButtonProps>) {
  const navigate = useNavigate()
  const loginWithPasskey = useAuthStore((state) => state.loginWithPasskey)
  const isLoading = useAuthStore((state) => state.isLoading)

  if (!browserSupportsWebAuthn()) {
    return null
  }

  const handleClick = async () => {
    const ok = await loginWithPasskey(accountId)
    if (ok) {
      toast.success("Signed in with passkey")
      navigate({ to: authRedirect || DEFAULT_AUTH_REDIRECT })
    }
  }

  return (
    <Button type="button" variant="outline" onClick={handleClick} disabled={isLoading} className={className}>
      {isLoading ? <Icons.Spinner className="mr-2 h-4 w-4 animate-spin" /> : <KeyRound className="mr-2 h-4 w-4" />}
      Sign in with Passkey
    </Button>
  )
}
