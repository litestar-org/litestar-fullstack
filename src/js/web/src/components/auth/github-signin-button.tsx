import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"

export const GITHUB_AUTH_REDIRECT_KEY = "github_auth_redirect"

type GitHubSignInVariant = "signin" | "signup" | "link"

const VARIANT_LABELS: Record<GitHubSignInVariant, string> = {
  signin: "Sign in with GitHub",
  signup: "Sign up with GitHub",
  link: "Link GitHub Account",
}

interface GitHubSignInButtonProps {
  variant?: GitHubSignInVariant
  onSuccess?: () => void
  redirectUrl?: string
  authRedirect?: string
  className?: string
}

export function GitHubSignInButton({ variant = "signin", onSuccess, redirectUrl, authRedirect, className }: Readonly<GitHubSignInButtonProps>) {
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

  return (
    <Button type="button" variant="outline" onClick={handleClick} className={className}>
      <Icons.GitHub className="mr-2 h-4 w-4" />
      {VARIANT_LABELS[variant]}
    </Button>
  )
}
