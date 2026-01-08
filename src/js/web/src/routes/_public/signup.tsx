import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { AuthForm } from "@/components/auth/auth-form"

export const Route = createFileRoute("/_public/signup")({
  validateSearch: (search) =>
    z
      .object({
        redirect: z.string().optional(),
      })
      .parse(search),
  component: SignupPage,
})

function SignupPage() {
  return (
    <div className="flex-1">
      <AuthForm />
    </div>
  )
}
