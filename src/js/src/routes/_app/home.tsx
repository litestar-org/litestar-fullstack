import { createFileRoute } from "@tanstack/react-router";
import { TeamList } from "@/components/teams/team-list";

export const Route = createFileRoute("/_app/home")({
  component: HomePage,
});

function HomePage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Your Teams</h1>
      <TeamList />
    </div>
  );
}
