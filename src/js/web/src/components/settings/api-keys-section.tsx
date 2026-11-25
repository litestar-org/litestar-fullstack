import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Copy, Key, Plus, RefreshCw, Trash2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useConfirmedAction } from "@/hooks/use-confirmed-action"
import { createApiKeyMutation, listApiKeysOptions, listApiKeysQueryKey, revokeApiKeyMutation, rotateApiKeyMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export function ApiKeysSection() {
  const queryClient = useQueryClient()
  const { data: keys = [], isLoading } = useQuery(listApiKeysOptions())
  const createKey = useMutation(createApiKeyMutation())
  const rotateKey = useMutation(rotateApiKeyMutation())
  const revokeKey = useMutation(revokeApiKeyMutation())
  const { runConfirmed, confirmationDialog } = useConfirmedAction()

  const [createOpen, setCreateOpen] = useState(false)
  const [name, setName] = useState("")
  const [scopesText, setScopesText] = useState("read,write,mcp")
  const [expiresInDays, setExpiresInDays] = useState("90")
  const [revealedSecret, setRevealedSecret] = useState<{ name: string; secret: string } | null>(null)

  const isBusy = createKey.isPending || rotateKey.isPending || revokeKey.isPending

  const handleCreate = () => {
    if (!name.trim()) {
      toast.error("Enter a name for the API key")
      return
    }
    const scopes = scopesText
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
    const parsedDays = Number.parseInt(expiresInDays, 10)
    void runConfirmed({
      failureTitle: "Unable to create API key",
      run: async (currentPassword) => {
        const issued = await createKey.mutateAsync({
          body: {
            name: name.trim(),
            scopes,
            expiresInDays: Number.isFinite(parsedDays) && parsedDays > 0 ? parsedDays : null,
            currentPassword,
          },
        })
        await queryClient.invalidateQueries({ queryKey: listApiKeysQueryKey() })
        setCreateOpen(false)
        setName("")
        setRevealedSecret({ name: issued.name, secret: issued.secret })
        toast.success("API key created")
      },
    })
  }

  const handleRotate = (keyId: string) =>
    void runConfirmed({
      failureTitle: "Unable to rotate API key",
      run: async (currentPassword) => {
        const rotated = await rotateKey.mutateAsync({ path: { key_id: keyId }, body: { currentPassword } })
        await queryClient.invalidateQueries({ queryKey: listApiKeysQueryKey() })
        setRevealedSecret({ name: rotated.name, secret: rotated.secret })
        toast.success("API key rotated")
      },
    })

  const handleRevoke = (keyId: string) =>
    void runConfirmed({
      failureTitle: "Unable to revoke API key",
      run: async (currentPassword) => {
        await revokeKey.mutateAsync({ path: { key_id: keyId }, body: { currentPassword } })
        await queryClient.invalidateQueries({ queryKey: listApiKeysQueryKey() })
        toast.success("API key revoked")
      },
    })

  const handleCopy = async () => {
    if (!revealedSecret) return
    await navigator.clipboard.writeText(revealedSecret.secret)
    toast.success("API key copied to clipboard")
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Personal API keys</CardTitle>
          <CardDescription>Create scoped bearer keys for MCP clients and programmatic access.</CardDescription>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Create API key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create API key</DialogTitle>
              <DialogDescription>Choose a descriptive label and scopes. The secret is shown only once.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <Input placeholder="Key name (e.g. MCP Desktop)" value={name} onChange={(event) => setName(event.target.value)} disabled={isBusy} />
              <Input placeholder="Scopes (comma-separated)" value={scopesText} onChange={(event) => setScopesText(event.target.value)} disabled={isBusy} />
              <Input
                type="number"
                min={1}
                placeholder="Expires in days (optional)"
                value={expiresInDays}
                onChange={(event) => setExpiresInDays(event.target.value)}
                disabled={isBusy}
              />
            </div>
            <DialogFooter>
              <Button onClick={handleCreate} disabled={isBusy || !name.trim()}>
                Create key
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading && <p className="text-muted-foreground text-sm">Loading API keys...</p>}
        {!isLoading && keys.length === 0 && <p className="text-muted-foreground text-sm">No API keys created yet.</p>}
        {!isLoading &&
          keys.map((key) => (
            <div key={key.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Key className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{key.name}</span>
                  <code className="rounded bg-muted px-1.5 py-0.5 text-xs">{key.prefix}...</code>
                  {key.revokedAt && <Badge variant="destructive">Revoked</Badge>}
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-muted-foreground text-xs">
                  {key.scopes.map((scope) => (
                    <Badge key={scope} variant="outline" className="text-[11px]">
                      {scope}
                    </Badge>
                  ))}
                  {key.expiresAt && <span>Expires {new Date(key.expiresAt).toLocaleDateString()}</span>}
                  {key.lastUsedAt && <span>· Last used {new Date(key.lastUsedAt).toLocaleDateString()}</span>}
                </div>
              </div>
              {!key.revokedAt && (
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleRotate(key.id)} disabled={isBusy}>
                    <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                    Rotate
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleRevoke(key.id)} disabled={isBusy}>
                    <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                    Revoke
                  </Button>
                </div>
              )}
            </div>
          ))}
      </CardContent>

      <Dialog
        open={revealedSecret !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRevealedSecret(null)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save your new API key</DialogTitle>
            <DialogDescription>
              This secret for <strong>{revealedSecret?.name}</strong> is shown once and cannot be retrieved again after closing this dialog.
            </DialogDescription>
          </DialogHeader>
          <Alert>
            <AlertDescription className="flex items-center justify-between gap-2">
              <code className="break-all font-mono text-xs">{revealedSecret?.secret}</code>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                <Copy className="mr-1.5 h-3.5 w-3.5" />
                Copy
              </Button>
            </AlertDescription>
          </Alert>
          <DialogFooter>
            <Button onClick={() => setRevealedSecret(null)}>I have saved this secret</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {confirmationDialog}
    </Card>
  )
}
