import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_public/terms")({
  component: TermsPage,
})

function TermsPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="mb-4 font-bold text-3xl">Terms of Service</h1>
      <p className="mb-2">This is a placeholder for your Terms of Service. Please update this page with your actual terms.</p>
    </div>
  )
}
