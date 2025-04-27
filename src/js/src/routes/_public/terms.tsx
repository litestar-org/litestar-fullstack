import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_public/terms")({
	component: TermsPage,
});

function TermsPage() {
	return (
		<div className="max-w-2xl mx-auto py-16 px-4">
			<h1 className="text-3xl font-bold mb-4">Terms of Service</h1>
			<p className="mb-2">
				This is a placeholder for your Terms of Service. Please update this page
				with your actual terms.
			</p>
		</div>
	);
}
