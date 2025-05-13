import { createFileRoute } from "@tanstack/react-router"

function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="mb-4 font-bold text-3xl">Privacy Policy</h1>
      <p className="mb-2">This is a placeholder for your Privacy Policy. Please update this page with your actual privacy policy content.</p>
    </div>
  )
}

export const Route = createFileRoute("/_public/privacy")({
  component: PrivacyPage,
})
