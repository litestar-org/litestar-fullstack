import { useEffect, useMemo, useState } from "react"
import { toast } from "sonner"
import { BackupCodesDisplay } from "@/components/mfa/backup-codes-display"
import { TotpInput } from "@/components/mfa/totp-input"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { useConfirmMfaSetup, useInitiateMfaSetup } from "@/lib/api/hooks/auth"
import type { MfaSetup } from "@/lib/generated/api"

interface MfaSetupDialogProps {
  disabled?: boolean
}

export function MfaSetupDialog({ disabled }: MfaSetupDialogProps) {
  const [open, setOpen] = useState(false)
  const [setup, setSetup] = useState<MfaSetup | null>(null)
  const [codes, setCodes] = useState<string[] | null>(null)
  const [code, setCode] = useState("")
  const initiate = useInitiateMfaSetup()
  const confirm = useConfirmMfaSetup()

  const isLoading = initiate.isPending || confirm.isPending

  useEffect(() => {
    if (!open) {
      setSetup(null)
      setCodes(null)
      setCode("")
      return
    }
    if (setup || initiate.isPending) {
      return
    }
    initiate
      .mutateAsync()
      .then((data) => setSetup(data))
      .catch((error) => {
        toast.error("Unable to start MFA setup", {
          description: error instanceof Error ? error.message : "Please try again",
        })
      })
  }, [open, initiate, setup])

  const handleConfirm = async () => {
    if (!code || code.length < 6) {
      toast.error("Enter the 6-digit code from your authenticator app")
      return
    }
    try {
      const result = await confirm.mutateAsync(code)
      setCodes(result.codes ?? [])
    } catch (error) {
      toast.error("Verification failed", {
        description: error instanceof Error ? error.message : "Check the code and try again",
      })
    }
  }

  const qrContent = useMemo(() => {
    if (initiate.isPending || !setup) {
      return (
        <div className="space-y-4">
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      )
    }
    return (
      <div className="space-y-4">
        <div className="flex justify-center rounded-lg border border-border/60 bg-muted/40 p-4">
          <img src={setup.qrCode} alt="MFA QR code" className="h-40 w-40" />
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/30 px-4 py-3 font-mono text-sm">{setup.secret}</div>
        <TotpInput value={code} onChange={setCode} disabled={isLoading} autoFocus />
      </div>
    )
  }, [setup, initiate.isPending, code, isLoading])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button disabled={disabled}>Enable MFA</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Enable multi-factor authentication</DialogTitle>
          <DialogDescription>Scan the QR code with your authenticator app, then enter the 6-digit verification code.</DialogDescription>
        </DialogHeader>
        {codes ? (
          <BackupCodesDisplay codes={codes} description="Save these codes in a secure place. Each code can be used once if you lose access to your authenticator." />
        ) : (
          qrContent
        )}
        <DialogFooter>
          {codes ? (
            <Button onClick={() => setOpen(false)}>Done</Button>
          ) : (
            <Button onClick={handleConfirm} disabled={isLoading || code.length < 6}>
              Verify &amp; finish
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
