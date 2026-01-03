import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"

interface OAuthLinkButtonProps {
  provider: "google" | "github"
  onClick: () => void
  disabled?: boolean
}

const providerLabels = {
  google: "Google",
  github: "GitHub",
}

export function OAuthLinkButton({ provider, onClick, disabled }: OAuthLinkButtonProps) {
  const Icon = provider === "google" ? Icons.google : Icons.gitHub
  return (
    <Button variant="outline" className="justify-start gap-2" onClick={onClick} disabled={disabled}>
      <Icon className="h-4 w-4" />
      Link {providerLabels[provider]}
    </Button>
  )
}
