import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useDisableMfa } from "@/lib/api/hooks/auth"

interface MfaDisableDialogProps {
  disabled?: boolean
}

export function MfaDisableDialog({ disabled }: MfaDisableDialogProps) {
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState("")
  const disableMfa = useDisableMfa()

  const handleDisable = async () => {
    if (!password) {
      toast.error("Enter your password to disable MFA")
      return
    }
    try {
      await disableMfa.mutateAsync(password)
      setOpen(false)
      setPassword("")
    } catch (error) {
      toast.error("Unable to disable MFA", {
        description: error instanceof Error ? error.message : "Check your password and try again",
      })
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" disabled={disabled}>
          Disable MFA
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disable multi-factor authentication</DialogTitle>
          <DialogDescription>Confirm your password to turn off MFA.</DialogDescription>
        </DialogHeader>
        <Input type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} />
        <DialogFooter>
          <Button onClick={handleDisable} disabled={disableMfa.isPending}>
            Disable MFA
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
