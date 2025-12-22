import { createFileRoute } from "@tanstack/react-router"

function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <div className="mb-8 space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Legal</p>
        <h1 className="font-['Space_Grotesk'] text-4xl font-semibold">Privacy Policy</h1>
        <p className="text-muted-foreground">How we collect, store, and use data inside the Litestar reference app.</p>
      </div>
      <div className="space-y-6 text-muted-foreground">
        <p>
          We collect only the information required to operate this reference application, including account details and security events needed to
          keep the platform reliable.
        </p>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Data collected</h3>
          <p>Account profile data, authentication events, team membership metadata, and operational diagnostics for queues and background jobs.</p>
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Retention</h3>
          <p>Logs and operational data are retained for a limited period and deleted automatically unless required for security investigations.</p>
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Third parties</h3>
          <p>We rely on infrastructure providers for hosting, email delivery, and monitoring. Data is shared only as necessary to provide service.</p>
        </div>
      </div>
    </div>
  )
}

export const Route = createFileRoute("/_public/privacy")({
  component: PrivacyPage,
})
