import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { AuthForm } from "@/components/auth/auth-form"

export const Route = createFileRoute("/_public/login")({
  validateSearch: (search) =>
    z
      .object({
        redirect: z.string().optional(),
      })
      .parse(search),
  component: LoginPage,
})

function LoginPage() {
  return (
    <div className="flex-1">
      <AuthForm />
    </div>
  )
}
