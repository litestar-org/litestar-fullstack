import { Link, useRouter } from "@tanstack/react-router"
import { Icons } from "@/components/icons"
import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

import { AuthHeroPanel } from "./auth-hero-panel"
import { UserLoginForm } from "./user-login-form"
import { UserSignupForm } from "./user-signup-form"

export function AuthForm() {
  const router = useRouter()
  const pathname = router.state.location.pathname

  const isLogin = pathname === "/login"

  return (
    <div className="container relative flex min-h-screen flex-col items-center justify-center md:grid lg:max-w-none lg:grid-cols-2 lg:px-0">
      {/* Toggle link in top right */}
      <Link to={isLogin ? "/signup" : "/login"} className={cn(buttonVariants({ variant: "ghost" }), "absolute top-4 right-4 md:top-8 md:right-8")}>
        {isLogin ? "Need an account?" : "Sign in"}
      </Link>

      {/* Left panel with RetroGrid */}
      <AuthHeroPanel title="Litestar Fullstack" description="Build high-performance web applications with Python and React. Seamless SPA experience powered by Vite." />

      {/* Right panel with form */}
      <div className="flex flex-col justify-center px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-87.5">
          <div className="flex flex-col space-y-2 text-center">
            <h1 className="flex items-center justify-center gap-2 font-semibold text-2xl tracking-tight">
              <Icons.sparkle className="h-5 w-5" />
              {isLogin ? "Welcome back" : "Create account"}
            </h1>
            <p className="text-muted-foreground text-sm">{isLogin ? "Enter your credentials to sign in to your account" : "Enter your details to create your account"}</p>
          </div>

          {isLogin ? <UserLoginForm /> : <UserSignupForm />}

          {isLogin && (
            <div className="text-center">
              <Link to="/forgot-password" className="text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline">
                Forgot your password?
              </Link>
            </div>
          )}

          <p className="px-8 text-center text-muted-foreground text-sm">
            By continuing, you agree to our{" "}
            <Link to="/terms" className="underline underline-offset-4 hover:text-primary">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link to="/privacy" className="underline underline-offset-4 hover:text-primary">
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  )
}
