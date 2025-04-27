import { CreateTeamForm } from "@/components/teams/create-team-form";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/teams/new")({
	component: NewTeamPage,
});

function NewTeamPage() {
	return (
		<div className="container mx-auto py-8">
			<h1 className="text-3xl font-bold mb-8">Create New Team</h1>
			<CreateTeamForm />
		</div>
	);
}
