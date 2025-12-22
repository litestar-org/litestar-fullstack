import { createFileRoute } from "@tanstack/react-router"
import { LandingPage } from "@/components/landing/landing-page"

export const Route = createFileRoute("/_public/landing")({
  component: LandingPage,
})
