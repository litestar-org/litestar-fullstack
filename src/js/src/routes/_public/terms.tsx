import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_public/terms")({
  component: TermsPage,
})

function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <div className="mb-8 space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Legal</p>
        <h1 className="font-['Space_Grotesk'] text-4xl font-semibold">Terms of Service</h1>
        <p className="text-muted-foreground">These terms govern your use of the Litestar reference application.</p>
      </div>
      <div className="space-y-6 text-muted-foreground">
        <p>
          By accessing the Litestar reference application you agree to use the service responsibly, follow applicable laws, and avoid any
          activity that could disrupt platform reliability or security.
        </p>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Usage</h3>
          <p>Use the service for legitimate product evaluation. Do not probe for vulnerabilities, overwhelm shared infrastructure, or resell access.</p>
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Data</h3>
          <p>Your account data remains yours. Operational logs are stored to keep the platform secure and are retained only as long as necessary.</p>
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Support</h3>
          <p>Support requests are handled on a best-effort basis during the public preview. Critical issues are prioritized within business hours.</p>
        </div>
      </div>
    </div>
  )
}
