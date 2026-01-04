import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { apiAuthOauthGithubGithubAuthorize } from "@/lib/generated/api"

interface GitHubSignInButtonProps {
  variant?: "signin" | "signup" | "link"
  onSuccess?: () => void
  onError?: (error: string) => void
  redirectUrl?: string
  className?: string
}

export function GitHubSignInButton({ variant = "signin", onSuccess, onError, redirectUrl, className }: GitHubSignInButtonProps) {
  const { mutate: initiateOAuth, isPending } = useMutation({
    mutationFn: async () => {
      const targetUrl = redirectUrl ?? `${window.location.origin}/auth/github/callback`
      const response = await apiAuthOauthGithubGithubAuthorize({
        query: {
          redirect_url: targetUrl,
        },
      })

      if (response.error) {
        throw new Error("Failed to initiate GitHub OAuth")
      }

      return response.data
    },
    onSuccess: (data) => {
      if (data?.authorizationUrl) {
        // Redirect to GitHub OAuth
        window.location.href = data.authorizationUrl
      } else {
        toast.error("Failed to get authorization URL")
        onError?.("Failed to get authorization URL")
      }
      onSuccess?.()
    },
    onError: (error: Error) => {
      const message = error.message || "Failed to sign in with GitHub"
      toast.error(message)
      onError?.(message)
    },
  })

  const handleClick = () => {
    initiateOAuth()
  }

  const getButtonText = () => {
    switch (variant) {
      case "signup":
        return "Sign up with GitHub"
      case "link":
        return "Link GitHub Account"
      default:
        return "Sign in with GitHub"
    }
  }

  return (
    <Button type="button" variant="outline" onClick={handleClick} disabled={isPending} className={className}>
      {isPending ? <Icons.spinner className="mr-2 h-4 w-4 animate-spin" /> : <Icons.gitHub className="mr-2 h-4 w-4" />}
      {getButtonText()}
    </Button>
  )
}
