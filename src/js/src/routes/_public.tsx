import { PublicLayout } from "@/layouts/public-layout";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_public")({
	component: PublicLayout,
});
