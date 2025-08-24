import { useEffect, useState } from "react"
import { useNavigate, useSearch } from "@tanstack/react-router"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/use-auth"

export const Route = createFileRoute("/_public/auth/google/callback")({
  component: GoogleCallbackPage,
})

function GoogleCallbackPage() {
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_public/auth/google/callback" })
  const { refetch: refetchUser } = useAuth()
  const [error, setError] = useState<string | null>(null)

  // Extract OAuth callback parameters
  const code = (searchParams as any).code as string | undefined
  const state = (searchParams as any).state as string | undefined
  const errorParam = (searchParams as any).error as string | undefined

  const { mutate: handleCallback, isPending } = useMutation({
    mutationFn: async () => {
      if (errorParam) {
        throw new Error(errorParam === "access_denied" 
          ? "You denied access to your Google account" 
          : `OAuth error: ${errorParam}`)
      }

      if (!code || !state) {
        throw new Error("Missing OAuth callback parameters")
      }

      // Call the backend callback endpoint
      const response = await fetch(`/api/auth/google/callback?code=${code}&state=${state}`, {
        method: "GET",
        credentials: "include",
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Authentication failed" }))
        throw new Error(errorData.detail || "Authentication failed")
      }

      return response.json()
    },
    onSuccess: async (data) => {
      // If we received auth tokens, the user is now logged in
      if (data.access_token) {
        // Store the token if needed (usually handled by auth context)
        localStorage.setItem("access_token", data.access_token)
        
        // Refetch user data
        await refetchUser()
        
        toast.success("Successfully signed in with Google!")
        
        // Redirect to dashboard or intended destination
        navigate({ to: "/home" })
      } else if (data.message) {
        toast.success(data.message)
        navigate({ to: "/home" })
      }
    },
    onError: (error: Error) => {
      setError(error.message)
      toast.error(error.message)
    },
  })

  useEffect(() => {
    // Automatically handle the callback when the component mounts
    if (code && state && !errorParam) {
      handleCallback()
    } else if (errorParam) {
      setError(errorParam === "access_denied" 
        ? "You denied access to your Google account" 
        : `Authentication failed: ${errorParam}`)
    } else if (!code || !state) {
      setError("Invalid OAuth callback - missing required parameters")
    }
  }, [code, state, errorParam])

  return (
    <div className="container flex h-screen w-screen flex-col items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">
            {isPending ? "Completing sign in..." : error ? "Authentication Failed" : "Processing..."}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isPending && (
            <div className="flex flex-col items-center space-y-4">
              <Icons.spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Please wait while we complete your sign in with Google...
              </p>
            </div>
          )}
          
          {error && (
            <>
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
              <div className="flex flex-col space-y-2">
                <Button
                  onClick={() => navigate({ to: "/login" })}
                  variant="default"
                  className="w-full"
                >
                  Back to Login
                </Button>
                <Button
                  onClick={() => window.location.href = "/api/auth/google"}
                  variant="outline"
                  className="w-full"
                >
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