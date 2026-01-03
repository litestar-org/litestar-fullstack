import { useMemo } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface BackupCodesDisplayProps {
  codes: string[]
  title?: string
  description?: string
}

export function BackupCodesDisplay({ codes, title = "Backup codes", description }: BackupCodesDisplayProps) {
  const formatted = useMemo(() => codes.filter(Boolean), [codes])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formatted.join("\n"))
      toast.success("Backup codes copied")
    } catch {
      toast.error("Unable to copy backup codes")
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          {description && <p className="text-muted-foreground text-sm">{description}</p>}
        </div>
        <Button variant="outline" size="sm" onClick={handleCopy}>
          Copy
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2 sm:grid-cols-2">
          {formatted.map((code) => (
            <div key={code} className="rounded-md border border-border/60 bg-muted/40 px-3 py-2 font-mono text-sm text-foreground">
              {code}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
