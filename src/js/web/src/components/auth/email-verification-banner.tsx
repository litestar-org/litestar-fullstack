import { useMutation } from "@tanstack/react-query"
import { AlertCircle, CheckCircle2, X } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/lib/auth"
import { localVerificationResendMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

interface EmailVerificationBannerProps {
  dismissible?: boolean
  className?: string
}

export function EmailVerificationBanner({ dismissible = false, className }: EmailVerificationBannerProps) {
  const user = useAuthStore((state) => state.user)
  const [isDismissed, setIsDismissed] = useState(false)
  const [lastSentAt, setLastSentAt] = useState<Date | null>(null)

  const { mutate: resendVerification, isPending } = useMutation({
    ...localVerificationResendMutation(),
    onSuccess: () => {
      setLastSentAt(new Date())
      toast.success("Verification email sent! Please check your inbox.")
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Failed to send verification email")
    },
  })

  const shouldHide = !user || user.isVerified || isDismissed
  if (shouldHide) {
    return null
  }

  const canResend = !lastSentAt || Date.now() - lastSentAt.getTime() > 60000

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
          <Button variant="outline" size="sm" onClick={() => resendVerification({ body: { identifier: user.email } })} disabled={isPending || !canResend}>
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
    <Alert variant="success">
      <CheckCircle2 className="h-4 w-4" />
      <AlertTitle>Email Verified Successfully!</AlertTitle>
      <AlertDescription>Your email has been verified. You now have full access to all features.</AlertDescription>
    </Alert>
  )
}
