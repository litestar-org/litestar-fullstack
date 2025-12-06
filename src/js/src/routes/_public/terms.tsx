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
      <div className="prose prose-invert prose-headings:text-foreground prose-p:text-muted-foreground">
        <p>This placeholder content should be replaced with your production-ready terms. Outline acceptable use, data handling, and support expectations.</p>
        <h3>Usage</h3>
        <p>Define what constitutes appropriate use of the application, rate limits, and prohibited activities.</p>
        <h3>Data</h3>
        <p>Clarify data ownership, storage locations, retention periods, and deletion policies.</p>
        <h3>Support</h3>
        <p>Describe how users can request help, expected response windows, and escalation paths.</p>
      </div>
    </div>
  )
}
