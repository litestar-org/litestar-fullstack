import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { CheckCircle2, XCircle } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"
import { z } from "zod"
import { AuthSplitLayout } from "@/components/auth/auth-hero-panel"
import { Icons } from "@/components/icons"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { extractApiErrorMessage } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import { localVerificationConfirmMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export const Route = createFileRoute("/_public/verify-email")({
  validateSearch: (search) =>
    z
      .object({
        token: z.string().optional(),
      })
      .parse(search),
  component: VerifyEmailPage,
})

const HOME_REDIRECT_DELAY_MS = 3000

function VerifyEmailPage() {
  const navigate = useNavigate()
  const { token } = useSearch({ from: "/_public/verify-email" })
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
  const [errorMessage, setErrorMessage] = useState("")
  const submittedTokenRef = useRef<string | null>(null)

  const { mutate: verifyEmail, isPending: isVerifying } = useMutation({
    ...localVerificationConfirmMutation(),
    onSuccess: async () => {
      setStatus("success")
      toast.success("Email verified successfully!")
      await checkAuth()
    },
    onError: (error) => {
      const message = extractApiErrorMessage(error, "Verification failed")
      setStatus("error")
      setErrorMessage(message)
      toast.error(message)
    },
  })

  useEffect(() => {
    if (!token) {
      setStatus("error")
      setErrorMessage("Verification token is missing")
      return
    }
    // The token is single-use, so a re-run of this effect must not submit it again.
    if (submittedTokenRef.current === token) {
      return
    }
    submittedTokenRef.current = token
    verifyEmail({ body: { token } })
  }, [token, verifyEmail])

  useEffect(() => {
    if (status !== "success") {
      return
    }
    const redirectTimer = setTimeout(() => void navigate({ to: "/home" }), HOME_REDIRECT_DELAY_MS)
    return () => clearTimeout(redirectTimer)
  }, [status, navigate])

  return (
    <AuthSplitLayout heroDescription="Verify your email to access all features.">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">
          {status === "verifying" && "Verifying your email..."}
          {status === "success" && "Email Verified!"}
          {status === "error" && "Verification Failed"}
        </h1>
      </div>

      {status === "verifying" && (
        <div className="flex flex-col items-center space-y-4">
          <Icons.Spinner className="h-8 w-8 animate-spin text-primary" />
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
                  <Button onClick={() => verifyEmail({ body: { token } })} variant="outline" className="w-full" disabled={isVerifying}>
                    Try Again
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </AuthSplitLayout>
  )
}
