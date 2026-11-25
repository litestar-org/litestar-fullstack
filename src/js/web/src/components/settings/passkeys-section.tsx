import { browserSupportsWebAuthn, startRegistration } from "@simplewebauthn/browser"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { KeyRound, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useAuthConfig, useStepUpGrant } from "@/lib/api/hooks/auth"
import { extractApiErrorMessage } from "@/lib/api-client"
import { useAuthStore } from "@/lib/auth"
import {
  passkeyListOptions,
  passkeyListQueryKey,
  passkeyRegistrationOptionsMutation,
  passkeyRegistrationVerifyMutation,
  passkeyRemoveMutation,
} from "@/lib/generated/api/@tanstack/react-query.gen"

export function PasskeysSection() {
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const { data: authConfig } = useAuthConfig()
  const { data: passkeys = [], isLoading } = useQuery(passkeyListOptions())
  const beginRegistration = useMutation(passkeyRegistrationOptionsMutation())
  const verifyRegistration = useMutation(passkeyRegistrationVerifyMutation())
  const removePasskey = useMutation(passkeyRemoveMutation())
  const { requestGrant, isPending: isStepUpPending } = useStepUpGrant()

  const [isRegisterDialogOpen, setIsRegisterDialogOpen] = useState(false)
  const [credentialIdToRemove, setCredentialIdToRemove] = useState<string | null>(null)
  const [password, setPassword] = useState("")

  if (authConfig?.passkeysEnabled === false) {
    return null
  }

  const isWebAuthnSupported = browserSupportsWebAuthn()
  const isBusy = isStepUpPending || beginRegistration.isPending || verifyRegistration.isPending || removePasskey.isPending

  const handleRegister = async () => {
    if (!password) {
      toast.error("Confirm your password to register a passkey")
      return
    }
    try {
      const grant = await requestGrant("passkey-register", password)
      const ceremony = await beginRegistration.mutateAsync({
        body: {
          step_up_grant: grant,
          user_name: user?.email ?? "account",
        },
      })
      const optionsJSON = JSON.parse(ceremony.options)
      const attestation = await startRegistration({ optionsJSON })
      await verifyRegistration.mutateAsync({
        body: {
          account_id: user?.id ?? "",
          binding: ceremony.binding ?? undefined,
          response: JSON.stringify(attestation),
        },
      })
      await queryClient.invalidateQueries({ queryKey: passkeyListQueryKey() })
      toast.success("Passkey registered")
      setIsRegisterDialogOpen(false)
      setPassword("")
    } catch (error) {
      if (error instanceof Error && (error.name === "AbortError" || error.name === "NotAllowedError")) {
        toast.info("Passkey registration was cancelled")
        return
      }
      toast.error("Unable to register passkey", {
        description: extractApiErrorMessage(error, "Please try again"),
      })
    }
  }

  const handleRemove = async () => {
    if (!credentialIdToRemove || !password) {
      toast.error("Confirm your password to remove this passkey")
      return
    }
    try {
      const grant = await requestGrant("passkey-remove", password)
      await removePasskey.mutateAsync({
        path: { credential_id: credentialIdToRemove },
        body: { step_up_grant: grant },
      })
      await queryClient.invalidateQueries({ queryKey: passkeyListQueryKey() })
      toast.success("Passkey removed")
      setCredentialIdToRemove(null)
      setPassword("")
    } catch (error) {
      toast.error("Unable to remove passkey", {
        description: extractApiErrorMessage(error, "Please try again"),
      })
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Passkeys</CardTitle>
          <CardDescription>Sign in securely with biometrics or a hardware security key.</CardDescription>
        </div>
        {isWebAuthnSupported && (
          <Dialog
            open={isRegisterDialogOpen}
            onOpenChange={(open) => {
              setIsRegisterDialogOpen(open)
              if (!open) setPassword("")
            }}
          >
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add passkey
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Register a new passkey</DialogTitle>
                <DialogDescription>Confirm your password, then follow your browser prompt to enroll your passkey.</DialogDescription>
              </DialogHeader>
              <Input type="password" placeholder="Current password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isBusy} />
              <DialogFooter>
                <Button onClick={handleRegister} disabled={isBusy || !password}>
                  Register passkey
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {!isWebAuthnSupported && <p className="text-muted-foreground text-sm">This browser does not support WebAuthn passkeys.</p>}
        {isLoading && <p className="text-muted-foreground text-sm">Loading passkeys...</p>}
        {!isLoading && passkeys.length === 0 && <p className="text-muted-foreground text-sm">No passkeys registered yet.</p>}
        {!isLoading &&
          passkeys.map((passkey) => (
            <div key={passkey.credential_id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
              <div className="flex items-center gap-3">
                <KeyRound className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="font-medium">{passkey.display_name || "Passkey"}</p>
                  <p className="text-muted-foreground text-xs">
                    Added {new Date(passkey.created_at).toLocaleDateString()}
                    {passkey.last_used_at ? ` · Last used ${new Date(passkey.last_used_at).toLocaleDateString()}` : ""}
                  </p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => setCredentialIdToRemove(passkey.credential_id)} disabled={isBusy}>
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Remove
              </Button>
            </div>
          ))}
      </CardContent>

      <Dialog
        open={credentialIdToRemove !== null}
        onOpenChange={(open) => {
          if (!open) {
            setCredentialIdToRemove(null)
            setPassword("")
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove passkey</DialogTitle>
            <DialogDescription>Confirm your password to permanently remove this passkey.</DialogDescription>
          </DialogHeader>
          <Input type="password" placeholder="Current password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isBusy} />
          <DialogFooter>
            <Button variant="destructive" onClick={handleRemove} disabled={isBusy || !password}>
              Remove passkey
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
