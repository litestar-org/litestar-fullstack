import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface BackupCodesDisplayProps {
  codes: string[]
  description: string
}

export function BackupCodesDisplay({ codes, description }: Readonly<BackupCodesDisplayProps>) {
  const nonEmptyCodes = codes.filter(Boolean)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(nonEmptyCodes.join("\n"))
      toast.success("Backup codes copied")
    } catch {
      toast.error("Unable to copy backup codes")
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Backup codes</CardTitle>
          <p className="text-muted-foreground text-sm">{description}</p>
        </div>
        <Button variant="outline" size="sm" onClick={handleCopy}>
          Copy
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2 sm:grid-cols-2">
          {nonEmptyCodes.map((code) => (
            <div key={code} className="rounded-md border border-border/60 bg-muted/40 px-3 py-2 font-mono text-sm text-foreground">
              {code}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
