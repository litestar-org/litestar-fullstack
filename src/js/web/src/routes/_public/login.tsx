import { createFileRoute } from "@tanstack/react-router"
import { AuthForm } from "@/components/auth/auth-form"

export const Route = createFileRoute("/_public/login")({
  component: LoginPage,
})

function LoginPage() {
  return (
    <div className="flex-1">
      <AuthForm />
    </div>
  )
}
