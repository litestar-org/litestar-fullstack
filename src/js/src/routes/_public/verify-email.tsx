import { useEffect, useState } from "react"
import { useNavigate, useSearch } from "@tanstack/react-router"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { CheckCircle2, XCircle, Mail } from "lucide-react"
import { client } from "@/lib/api/client"
import { useAuth } from "@/hooks/use-auth"

export const Route = createFileRoute("/_public/verify-email")({
  component: VerifyEmailPage,
})

function VerifyEmailPage() {
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_public/verify-email" })
  const { refetch: refetchUser } = useAuth()
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
  const [errorMessage, setErrorMessage] = useState<string>("")

  // Extract token from URL
  const token = (searchParams as any).token as string | undefined

  const { mutate: verifyEmail } = useMutation({
    mutationFn: async (verificationToken: string) => {
      const response = await client.GET("/api/access/verify-email", {
        params: {
          query: { token: verificationToken },
        },
      })

      if (response.error) {
        throw new Error(response.error.detail || "Verification failed")
      }

      return response.data
    },
    onSuccess: async () => {
      setStatus("success")
      toast.success("Email verified successfully!")
      
      // Refetch user data to update verification status
      await refetchUser()
      
      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        navigate({ to: "/home" })
      }, 3000)
    },
    onError: (error: Error) => {
      setStatus("error")
      setErrorMessage(error.message)
      toast.error(error.message)
    },
  })

  useEffect(() => {
    if (token) {
      verifyEmail(token)
    } else {
      setStatus("error")
      setErrorMessage("Verification token is missing")
    }
  }, [token])

  return (
    <div className="container flex h-screen w-screen flex-col items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">
            {status === "verifying" && "Verifying your email..."}
            {status === "success" && "Email Verified!"}
            {status === "error" && "Verification Failed"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {status === "verifying" && (
            <div className="flex flex-col items-center space-y-4">
              <Icons.spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Please wait while we verify your email address...
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center space-y-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-center">
                <p className="mb-2 font-medium">Your email has been verified successfully!</p>
                <p className="text-sm text-muted-foreground">
                  You will be redirected to the home page shortly...
                </p>
              </div>
              <Button
                onClick={() => navigate({ to: "/home" })}
                className="w-full"
              >
                Go to Home
              </Button>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center space-y-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
                <XCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <Alert variant="destructive">
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
              <div className="flex flex-col space-y-2 w-full">
                {errorMessage.includes("expired") ? (
                  <>
                    <p className="text-sm text-center text-muted-foreground mb-2">
                      Your verification link has expired. Please request a new one.
                    </p>
                    <Button
                      onClick={() => navigate({ to: "/login" })}
                      className="w-full"
                    >
                      Go to Login
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      onClick={() => navigate({ to: "/login" })}
                      variant="default"
                      className="w-full"
                    >
                      Back to Login
                    </Button>
                    <Button
                      onClick={() => window.location.reload()}
                      variant="outline"
                      className="w-full"
                    >
                      Try Again
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function ResendVerificationPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [hasSent, setHasSent] = useState(false)

  const { mutate: resendVerification, isPending } = useMutation({
    mutationFn: async () => {
      const response = await client.POST("/api/access/send-verification", {})
      if (response.error) {
        throw new Error(response.error.detail || "Failed to send verification email")
      }
      return response.data
    },
    onSuccess: () => {
      setHasSent(true)
      toast.success("Verification email sent! Please check your inbox.")
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to send verification email")
    },
  })

  if (hasSent) {
    return (
      <div className="container flex h-screen w-screen flex-col items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
              <Mail className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <CardTitle>Check your email</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="mb-4 text-sm text-muted-foreground">
              We've sent a verification link to <strong>{user?.email}</strong>
            </p>
            <Button
              onClick={() => navigate({ to: "/home" })}
              className="w-full"
            >
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container flex h-screen w-screen flex-col items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Verify Your Email</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-sm text-muted-foreground">
            Your email address <strong>{user?.email}</strong> needs to be verified 
            to access all features.
          </p>
          <Button
            onClick={() => resendVerification()}
            disabled={isPending}
            className="w-full"
          >
            {isPending ? "Sending..." : "Send Verification Email"}
          </Button>
          <Button
            onClick={() => navigate({ to: "/home" })}
            variant="outline"
            className="w-full"
          >
            Skip for now
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}