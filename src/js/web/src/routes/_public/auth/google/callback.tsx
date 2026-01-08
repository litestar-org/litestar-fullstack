import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { GOOGLE_AUTH_REDIRECT_KEY } from "@/components/auth/google-signin-button"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from "@/hooks/use-auth"
import { getSafeRedirectUrl } from "@/lib/redirect-utils"

export const Route = createFileRoute("/_public/auth/google/callback")({
  validateSearch: (search) =>
    z
      .object({
        token: z.string().optional(),
        // TanStack Router parses "true"/"false" as booleans, coerce to string
        is_new: z.coerce.string().optional(),
        error: z.string().optional(),
        message: z.string().optional(),
      })
      .parse(search),
  component: GoogleCallbackPage,
})

function GoogleCallbackPage() {
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_public/auth/google/callback" })
  const { refetch: refetchUser } = useAuth()
  const [error, setError] = useState<string | null>(null)

  const token = searchParams.token
  const errorParam = searchParams.error
  const message = searchParams.message

  useEffect(() => {
    const run = async () => {
      if (errorParam) {
        const errorMessage = errorParam === "access_denied" ? "You denied access to your Google account" : `Authentication failed: ${errorParam}`
        setError(errorMessage)
        toast.error(errorMessage)
        return
      }

      if (!token) {
        const errorMessage = message || "Invalid OAuth callback - missing token"
        setError(errorMessage)
        toast.error(errorMessage)
        return
      }

      localStorage.setItem("access_token", token)
      await refetchUser()
      toast.success("Successfully signed in with Google!")

      // Get and clear stored redirect destination
      const storedRedirect = sessionStorage.getItem(GOOGLE_AUTH_REDIRECT_KEY)
      sessionStorage.removeItem(GOOGLE_AUTH_REDIRECT_KEY)
      const finalRedirect = getSafeRedirectUrl(storedRedirect)

      navigate({ to: finalRedirect })
    }

    run()
  }, [errorParam, message, navigate, refetchUser, token])

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
        <CardHeader>
          <CardTitle className="text-center">{error ? "Authentication Failed" : "Completing sign in..."}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!error && (
            <div className="flex flex-col items-center space-y-4">
              <Icons.spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-muted-foreground text-sm">Please wait while we complete your sign in with Google...</p>
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
