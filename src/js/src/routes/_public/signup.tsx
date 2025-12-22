import { createFileRoute } from "@tanstack/react-router"
import { AuthForm } from "@/components/auth/auth-form"

export const Route = createFileRoute("/_public/signup")({
  component: SignupPage,
})

function SignupPage() {
  return (
    <div className="flex-1">
      <AuthForm />
    </div>
  )
}
