import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { CheckCircle2, Mail, XCircle } from "lucide-react"
import { useEffect, useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { AuthHeroPanel } from "@/components/auth/auth-hero-panel"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
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
      await refetchUser()
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
    <div className="relative flex min-h-screen w-full">
      <AuthHeroPanel showTestimonial={false} description="Verify your email to access all features." />
      <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-semibold tracking-tight">
              {status === "verifying" && "Verifying your email..."}
              {status === "success" && "Email Verified!"}
              {status === "error" && "Verification Failed"}
            </h1>
          </div>

          {status === "verifying" && (
            <div className="flex flex-col items-center space-y-4">
              <Icons.spinner className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Please wait while we verify your email address...</p>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center space-y-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-center">
                <p className="mb-2 font-medium">Your email has been verified successfully!</p>
                <p className="text-sm text-muted-foreground">You will be redirected to the home page shortly...</p>
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
                    <p className="mb-2 text-center text-sm text-muted-foreground">Your verification link has expired. Please request a new one.</p>
                    <Button onClick={() => navigate({ to: "/login" })} className="w-full">
                      Go to Login
                    </Button>
                  </>
                ) : (
                  <>
                    <Button onClick={() => navigate({ to: "/login" })} className="w-full">
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
        </div>
      </div>
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
      const response = await apiEmailVerificationRequestRequestVerification({
        body: { email: user.email },
      })
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
      <div className="relative flex min-h-screen w-full">
        <AuthHeroPanel showTestimonial={false} description="Verify your email to access all features." />
        <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900">
                <Mail className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h1 className="text-2xl font-semibold tracking-tight">Check your email</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                We've sent a verification link to <strong>{user?.email}</strong>
              </p>
            </div>
            <Button onClick={() => navigate({ to: "/home" })} className="w-full">
              Go to Home
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-screen w-full">
      <AuthHeroPanel showTestimonial={false} description="Verify your email to access all features." />
      <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-semibold tracking-tight">Verify Your Email</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Your email address <strong>{user?.email}</strong> needs to be verified to access all features.
            </p>
          </div>
          <div className="space-y-2">
            <Button onClick={() => resendVerification()} disabled={isPending} className="w-full">
              {isPending ? "Sending..." : "Send Verification Email"}
            </Button>
            <Button onClick={() => navigate({ to: "/home" })} variant="outline" className="w-full">
              Skip for now
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
