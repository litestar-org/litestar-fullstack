import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

interface ConfirmPasswordDialogProps {
  isBusy: boolean
  onConfirm: (password: string) => void
  onCancel: () => void
}

export function ConfirmPasswordDialog({ isBusy, onConfirm, onCancel }: Readonly<ConfirmPasswordDialogProps>) {
  const [password, setPassword] = useState("")

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onCancel()
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm your password</DialogTitle>
          <DialogDescription>It has been a while since you signed in. Enter your password to continue.</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault()
            onConfirm(password)
          }}
        >
          <Input
            type="password"
            autoComplete="current-password"
            placeholder="Current password"
            aria-label="Current password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={isBusy}
          />
          <DialogFooter>
            <Button type="submit" disabled={isBusy || !password}>
              Continue
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
