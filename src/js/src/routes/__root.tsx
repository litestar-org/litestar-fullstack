import { createRootRoute, Outlet } from "@tanstack/react-router";

export const Route = createRootRoute({
	component: RootRoute,
});

function RootRoute() {
	return (
		<div className="min-h-screen bg-background">
			<main className="container mx-auto py-4">
				<Outlet />
			</main>
		</div>
	);
}
