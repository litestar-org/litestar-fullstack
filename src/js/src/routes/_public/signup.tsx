import { createFileRoute } from "@tanstack/react-router";
import { SignupForm } from "@/components/auth/signup-form";

export const Route = createFileRoute("/_public/signup")({
  component: SignupPage,
});

function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignupForm />
    </div>
  );
}
