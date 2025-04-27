import { TeamList } from "@/components/teams/team-list";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/teams/")({
	component: TeamList,
});
