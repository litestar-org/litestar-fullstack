import { useState } from "react"
import { toast } from "sonner"
import { BackupCodesDisplay } from "@/components/mfa/backup-codes-display"
import { MfaDisableDialog } from "@/components/mfa/mfa-disable-dialog"
import { MfaSetupDialog } from "@/components/mfa/mfa-setup-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { SkeletonCard } from "@/components/ui/skeleton"
import { useMfaStatus, useRegenerateBackupCodes } from "@/lib/api/hooks/auth"

export function MfaSection() {
  const { data, isLoading, isError } = useMfaStatus()
  const regenerate = useRegenerateBackupCodes()
  const [regenOpen, setRegenOpen] = useState(false)
  const [regenPassword, setRegenPassword] = useState("")
  const [regenCodes, setRegenCodes] = useState<string[] | null>(null)

  if (isLoading) {
    return <SkeletonCard />
  }

  if (isError || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Multi-factor authentication</CardTitle>
          <CardDescription>We could not load MFA status.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const handleRegenerate = async () => {
    if (!regenPassword) {
      toast.error("Enter your password to regenerate backup codes")
      return
    }
    try {
      const result = await regenerate.mutateAsync(regenPassword)
      setRegenCodes(result.codes ?? [])
    } catch (error) {
      toast.error("Unable to regenerate codes", {
        description: error instanceof Error ? error.message : "Try again later",
      })
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Multi-factor authentication</CardTitle>
        <CardDescription>
          {data.enabled ? "MFA is enabled on your account." : "Add an extra layer of security to your account."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {data.enabled ? (
          <div className="flex flex-wrap gap-2">
            <MfaDisableDialog />
            <Button variant="outline" onClick={() => setRegenOpen(true)}>
              Regenerate backup codes
            </Button>
          </div>
        ) : (
          <MfaSetupDialog />
        )}
        {data.enabled && data.backup_codes_remaining !== null && (
          <p className="text-muted-foreground text-sm">
            Backup codes remaining: {data.backup_codes_remaining ?? 0}
          </p>
        )}
      </CardContent>
      <Dialog open={regenOpen} onOpenChange={setRegenOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Regenerate backup codes</DialogTitle>
            <DialogDescription>Confirm your password to generate a fresh set of codes.</DialogDescription>
          </DialogHeader>
          {regenCodes ? (
            <BackupCodesDisplay
              codes={regenCodes}
              description="These codes replace your previous set. Store them securely."
            />
          ) : (
            <Input
              type="password"
              placeholder="Password"
              value={regenPassword}
              onChange={(event) => setRegenPassword(event.target.value)}
            />
          )}
          <DialogFooter>
            {regenCodes ? (
              <Button onClick={() => setRegenOpen(false)}>Done</Button>
            ) : (
              <Button onClick={handleRegenerate} disabled={regenerate.isPending}>
                Regenerate
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
