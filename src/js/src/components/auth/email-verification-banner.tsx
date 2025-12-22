import { useMutation } from "@tanstack/react-query"
import { AlertCircle, CheckCircle2, X } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/use-auth"
import { apiEmailVerificationRequestRequestVerification } from "@/lib/generated/api"

interface EmailVerificationBannerProps {
  dismissible?: boolean
  className?: string
}

export function EmailVerificationBanner({ dismissible = false, className }: EmailVerificationBannerProps) {
  const { user } = useAuth()
  const [isDismissed, setIsDismissed] = useState(false)
  const [lastSentAt, setLastSentAt] = useState<Date | null>(null)

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
      setLastSentAt(new Date())
      toast.success("Verification email sent! Please check your inbox.")
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to send verification email")
    },
  })

  const shouldHide = !user || user.is_verified || isDismissed
  if (shouldHide) {
    return null
  }

  const canResend = !lastSentAt || Date.now() - lastSentAt.getTime() > 60000 // 1 minute cooldown

  return (
    <Alert className={className} variant="warning">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle className="flex items-center justify-between">
        <span>Email Verification Required</span>
        {dismissible && (
          <Button variant="ghost" size="icon" className="h-4 w-4 p-0" onClick={() => setIsDismissed(true)}>
            <X className="h-3 w-3" />
          </Button>
        )}
      </AlertTitle>
      <AlertDescription className="mt-2">
        <p className="mb-2">
          Please verify your email address to access all features. Check your inbox for a verification link sent to <strong>{user.email}</strong>.
        </p>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => resendVerification()} disabled={isPending || !canResend}>
            {isPending ? "Sending..." : "Resend verification email"}
          </Button>
          {lastSentAt && !canResend && <span className="text-muted-foreground text-xs">Please wait before requesting another email</span>}
        </div>
      </AlertDescription>
    </Alert>
  )
}

export function EmailVerificationSuccess() {
  return (
    <Alert className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
      <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
      <AlertTitle className="text-green-800 dark:text-green-200">Email Verified Successfully!</AlertTitle>
      <AlertDescription className="text-green-700 dark:text-green-300">Your email has been verified. You now have full access to all features.</AlertDescription>
    </Alert>
  )
}
