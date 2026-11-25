import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { GITHUB_AUTH_REDIRECT_KEY, startGitHubSignIn } from "@/components/auth/github-signin-button"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuthStore } from "@/lib/auth"
import { getSafeRedirectUrl } from "@/lib/redirect-utils"

export const Route = createFileRoute("/_public/auth/github/callback")({
  validateSearch: (search) =>
    z
      .object({
        error: z.string().optional(),
        message: z.string().optional(),
      })
      .parse(search),
  component: GitHubCallbackPage,
})

function GitHubCallbackPage() {
  const navigate = useNavigate()
  const { error: providerError, message: providerMessage } = useSearch({ from: "/_public/auth/github/callback" })
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const [failureMessage, setFailureMessage] = useState<string | null>(null)

  useEffect(() => {
    const reportFailure = (message: string) => {
      setFailureMessage(message)
      toast.error(message)
    }

    const completeSignIn = async () => {
      if (providerError) {
        reportFailure(providerError === "access_denied" ? "You denied access to your GitHub account" : `Authentication failed: ${providerError}`)
        return
      }

      try {
        const isAuthenticated = await checkAuth()
        if (!isAuthenticated) {
          reportFailure(providerMessage || "Could not verify your GitHub sign-in session. Please try again.")
          return
        }

        toast.success("Successfully signed in with GitHub!")
        const storedRedirect = sessionStorage.getItem(GITHUB_AUTH_REDIRECT_KEY)
        sessionStorage.removeItem(GITHUB_AUTH_REDIRECT_KEY)
        await navigate({ to: getSafeRedirectUrl(storedRedirect) })
      } catch (error) {
        reportFailure(error instanceof Error ? error.message : "Unable to complete GitHub sign-in")
      }
    }

    void completeSignIn()
  }, [checkAuth, providerError, providerMessage, navigate])

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
        <CardHeader>
          <CardTitle className="text-center">{failureMessage ? "Authentication Failed" : "Completing sign in..."}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!failureMessage && (
            <div className="flex flex-col items-center space-y-4">
              <Icons.Spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground text-sm">Please wait while we complete your sign in with GitHub...</p>
            </div>
          )}

          {failureMessage && (
            <>
              <Alert variant="destructive">
                <AlertDescription>{failureMessage}</AlertDescription>
              </Alert>
              <div className="flex flex-col space-y-2">
                <Button onClick={() => navigate({ to: "/login" })} variant="default" className="w-full">
                  Back to Login
                </Button>
                <Button onClick={startGitHubSignIn} variant="outline" className="w-full">
                  Try Again
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
