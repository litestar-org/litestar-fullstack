import { createFileRoute } from "@tanstack/react-router";

function PrivacyPage() {
  return (
    <div className="max-w-2xl mx-auto py-16 px-4">
      <h1 className="text-3xl font-bold mb-4">Privacy Policy</h1>
      <p className="mb-2">This is a placeholder for your Privacy Policy. Please update this page with your actual privacy policy content.</p>
    </div>
  );
}

export const Route = createFileRoute("/_public/privacy")({
  component: PrivacyPage,
});
