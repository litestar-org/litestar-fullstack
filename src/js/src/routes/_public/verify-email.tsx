import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { CheckCircle2, Mail, XCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from "@/hooks/use-auth"
import { apiEmailVerificationRequestRequestVerification, apiEmailVerificationVerifyVerifyEmail } from "@/lib/generated/api"

export const Route = createFileRoute("/_public/verify-email")({
  validateSearch: (search) =>
    z
      .object({
        token: z.string().optional(),
      })
      .parse(search),
  component: VerifyEmailPage,
})

function VerifyEmailPage() {
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_public/verify-email" })
  const { refetch: refetchUser } = useAuth()
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
  const [errorMessage, setErrorMessage] = useState<string>("")

  // Extract token from URL
  const token = searchParams.token

  const { mutate: verifyEmail, isPending: isVerifying } = useMutation({
    mutationFn: async (verificationToken: string) => {
      const response = await apiEmailVerificationVerifyVerifyEmail({
        body: { token: verificationToken },
      })

      if (response.error) {
        throw new Error((response.error as any).detail || "Verification failed")
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
  }, [token, verifyEmail])

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
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
              <p className="text-muted-foreground text-sm">Please wait while we verify your email address...</p>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center space-y-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-center">
                <p className="mb-2 font-medium">Your email has been verified successfully!</p>
                <p className="text-muted-foreground text-sm">You will be redirected to the home page shortly...</p>
              </div>
              <Button onClick={() => navigate({ to: "/home" })} className="w-full">
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
              <div className="flex w-full flex-col space-y-2">
                {errorMessage.includes("expired") ? (
                  <>
                    <p className="mb-2 text-center text-muted-foreground text-sm">Your verification link has expired. Please request a new one.</p>
                    <Button onClick={() => navigate({ to: "/login" })} className="w-full">
                      Go to Login
                    </Button>
                  </>
                ) : (
                  <>
                    <Button onClick={() => navigate({ to: "/login" })} variant="default" className="w-full">
                      Back to Login
                    </Button>
                    {token && (
                      <Button onClick={() => verifyEmail(token)} variant="outline" className="w-full" disabled={isVerifying}>
                        Try Again
                      </Button>
                    )}
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
      if (!user?.email) {
        throw new Error("User email not available")
      }
      const response = await apiEmailVerificationRequestRequestVerification({ body: { email: user.email } })
      if (response.error) {
        throw new Error((response.error as any).detail || "Failed to send verification email")
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
      <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
        <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
              <Mail className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <CardTitle>Check your email</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="mb-4 text-muted-foreground text-sm">
              We've sent a verification link to <strong>{user?.email}</strong>
            </p>
            <Button onClick={() => navigate({ to: "/home" })} className="w-full">
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md border-border/60 bg-card/80 shadow-xl shadow-primary/15">
        <CardHeader className="text-center">
          <CardTitle>Verify Your Email</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-muted-foreground text-sm">
            Your email address <strong>{user?.email}</strong> needs to be verified to access all features.
          </p>
          <Button onClick={() => resendVerification()} disabled={isPending} className="w-full">
            {isPending ? "Sending..." : "Send Verification Email"}
          </Button>
          <Button onClick={() => navigate({ to: "/home" })} variant="outline" className="w-full">
            Skip for now
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
