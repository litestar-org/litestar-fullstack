import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"

export const GITHUB_AUTH_REDIRECT_KEY = "github_auth_redirect"

interface GitHubSignInButtonProps {
  variant?: "signin" | "signup" | "link"
  onSuccess?: () => void
  onError?: (error: string) => void
  redirectUrl?: string
  authRedirect?: string
  className?: string
}

export function GitHubSignInButton({ variant = "signin", onSuccess, redirectUrl, authRedirect, className }: GitHubSignInButtonProps) {
  const handleClick = () => {
    if (authRedirect) {
      sessionStorage.setItem(GITHUB_AUTH_REDIRECT_KEY, authRedirect)
    } else {
      sessionStorage.removeItem(GITHUB_AUTH_REDIRECT_KEY)
    }
    const returnTo = redirectUrl ?? "/auth/github/callback"
    onSuccess?.()
    window.location.assign(`/api/auth/oauth/github/login?return_to=${encodeURIComponent(returnTo)}`)
  }

  const label = variant === "signup" ? "Sign up with GitHub" : variant === "link" ? "Link GitHub Account" : "Sign in with GitHub"

  return (
    <Button type="button" variant="outline" onClick={handleClick} className={className}>
      <Icons.gitHub className="mr-2 h-4 w-4" />
      {label}
    </Button>
  )
}
