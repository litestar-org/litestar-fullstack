import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"

interface GoogleSignInButtonProps {
  variant?: "signin" | "signup" | "link"
  onSuccess?: () => void
  onError?: (error: string) => void
  redirectUrl?: string
  className?: string
}

export function GoogleSignInButton({ variant = "signin", onSuccess, onError, redirectUrl, className }: GoogleSignInButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  const { mutate: initiateOAuth } = useMutation({
    mutationFn: async () => {
      // The backend OAuth endpoint expects a GET request to /api/auth/google
      // We'll construct the URL with optional redirect parameter
      const params = new URLSearchParams()
      if (redirectUrl) {
        params.append("redirect_url", redirectUrl)
      }

      const url = `/api/auth/google${params.toString() ? `?${params.toString()}` : ""}`
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
      })

      if (!response.ok) {
        throw new Error("Failed to initiate OAuth")
      }

      return response.json()
    },
    onSuccess: (data) => {
      if (data.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = data.authorization_url
      } else {
        toast.error("Failed to get authorization URL")
        onError?.("Failed to get authorization URL")
      }
      onSuccess?.()
    },
    onError: (error: Error) => {
      setIsLoading(false)
      const message = error.message || "Failed to sign in with Google"
      toast.error(message)
      onError?.(message)
    },
  })

  const handleClick = () => {
    setIsLoading(true)
    initiateOAuth()
  }

  const getButtonText = () => {
    switch (variant) {
      case "signup":
        return "Sign up with Google"
      case "link":
        return "Link Google Account"
      default:
        return "Sign in with Google"
    }
  }

  return (
    <Button type="button" variant="outline" onClick={handleClick} disabled={isLoading} className={className}>
      {isLoading ? (
        <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
      ) : (
        <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
          <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
          <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
          <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
          <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
      )}
      {getButtonText()}
    </Button>
  )
}
