import { createFileRoute } from "@tanstack/react-router"

function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <div className="mb-8 space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">Legal</p>
        <h1 className="font-['Space_Grotesk'] text-4xl font-semibold">Privacy Policy</h1>
        <p className="text-muted-foreground">How we collect, store, and use data inside the Litestar reference app.</p>
      </div>
      <div className="prose prose-invert prose-headings:text-foreground prose-p:text-muted-foreground">
        <p>Replace this placeholder with your production-ready policy. Be explicit about metrics, logs, and PII handling.</p>
        <h3>Data collected</h3>
        <p>List account data (email, name), authentication events, queue/job metadata, and diagnostic logs.</p>
        <h3>Retention</h3>
        <p>Clarify how long data is retained and how users can request removal.</p>
        <h3>Third parties</h3>
        <p>Note any external services (email providers, object storage, analytics) and what is shared.</p>
      </div>
    </div>
  )
}

export const Route = createFileRoute("/_public/privacy")({
  component: PrivacyPage,
})
