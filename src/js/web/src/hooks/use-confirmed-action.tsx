import { useState } from "react"
import { toast } from "sonner"
import { ConfirmPasswordDialog } from "@/components/auth/confirm-password-dialog"
import { extractApiErrorMessage, isReauthenticationRequired } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"

export interface ConfirmedAction {
  failureTitle: string
  run: (currentPassword?: string) => Promise<void>
}

export function useConfirmedAction() {
  const hasPassword = useAuthStore((state) => state.user?.hasPassword ?? true)
  const [pending, setPending] = useState<ConfirmedAction | null>(null)
  const [isConfirming, setIsConfirming] = useState(false)

  const attempt = async (action: ConfirmedAction, currentPassword?: string) => {
    try {
      await action.run(currentPassword)
      setPending(null)
    } catch (error) {
      if (currentPassword === undefined && isReauthenticationRequired(error)) {
        if (hasPassword) {
          setPending(action)
        } else {
          toast.error("Sign in again to continue", { description: "This action needs a recent sign-in." })
        }
        return
      }
      toast.error(action.failureTitle, { description: extractApiErrorMessage(error, "Please try again") })
    }
  }

  const confirm = async (action: ConfirmedAction, password: string) => {
    setIsConfirming(true)
    try {
      await attempt(action, password)
    } finally {
      setIsConfirming(false)
    }
  }

  return {
    runConfirmed: (action: ConfirmedAction) => attempt(action),
    confirmationDialog: pending ? (
      <ConfirmPasswordDialog isBusy={isConfirming} onConfirm={(password) => void confirm(pending, password)} onCancel={() => setPending(null)} />
    ) : null,
  }
}
