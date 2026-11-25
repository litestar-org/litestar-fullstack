import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"

export const GITHUB_AUTH_REDIRECT_KEY = "github_auth_redirect"

type GitHubSignInVariant = "signin" | "signup" | "link"

const VARIANT_LABELS: Record<GitHubSignInVariant, string> = {
  signin: "Sign in with GitHub",
  signup: "Sign up with GitHub",
  link: "Link GitHub Account",
}

const GITHUB_CALLBACK_PATH = "/auth/github/callback"

/** Sends the browser to GitHub; the provider returns it to the callback page. */
export function startGitHubSignIn() {
  window.location.assign(`/api/auth/oauth/github/login?return_to=${encodeURIComponent(GITHUB_CALLBACK_PATH)}`)
}

interface GitHubSignInButtonProps {
  variant?: GitHubSignInVariant
  authRedirect?: string
  className?: string
}

export function GitHubSignInButton({ variant = "signin", authRedirect, className }: Readonly<GitHubSignInButtonProps>) {
  const handleClick = () => {
    if (authRedirect) {
      sessionStorage.setItem(GITHUB_AUTH_REDIRECT_KEY, authRedirect)
    } else {
      sessionStorage.removeItem(GITHUB_AUTH_REDIRECT_KEY)
    }
    startGitHubSignIn()
  }

  return (
    <Button type="button" variant="outline" onClick={handleClick} className={className}>
      <Icons.GitHub className="mr-2 h-4 w-4" />
      {VARIANT_LABELS[variant]}
    </Button>
  )
}
