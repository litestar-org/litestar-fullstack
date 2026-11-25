import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { GITHUB_AUTH_REDIRECT_KEY } from "@/components/auth/github-signin-button"
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
  const searchParams = useSearch({ from: "/_public/auth/github/callback" })
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const [error, setError] = useState<string | null>(null)

  const errorParam = searchParams.error
  const message = searchParams.message

  useEffect(() => {
    const run = async () => {
      if (errorParam) {
        const errorMessage = errorParam === "access_denied" ? "You denied access to your GitHub account" : `Authentication failed: ${errorParam}`
        setError(errorMessage)
        toast.error(errorMessage)
        return
      }

      try {
        const authenticated = await checkAuth()
        if (!authenticated) {
          const errorMessage = message || "Could not verify your GitHub sign-in session. Please try again."
          setError(errorMessage)
          toast.error(errorMessage)
          return
        }

        toast.success("Successfully signed in with GitHub!")
        const storedRedirect = sessionStorage.getItem(GITHUB_AUTH_REDIRECT_KEY)
        sessionStorage.removeItem(GITHUB_AUTH_REDIRECT_KEY)
        await navigate({ to: getSafeRedirectUrl(storedRedirect) })
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unable to complete GitHub sign-in"
        setError(errorMessage)
        toast.error(errorMessage)
      }
    }

    void run()
  }, [checkAuth, errorParam, message, navigate])

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
        <CardHeader>
          <CardTitle className="text-center">{error ? "Authentication Failed" : "Completing sign in..."}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!error && (
            <div className="flex flex-col items-center space-y-4">
              <Icons.Spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground text-sm">Please wait while we complete your sign in with GitHub...</p>
            </div>
          )}

          {error && (
            <>
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
              <div className="flex flex-col space-y-2">
                <Button onClick={() => navigate({ to: "/login" })} variant="default" className="w-full">
                  Back to Login
                </Button>
                <Button onClick={() => navigate({ to: "/login" })} variant="outline" className="w-full">
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
