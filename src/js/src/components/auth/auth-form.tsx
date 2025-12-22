import { Link, useRouter } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/lib/theme-context"

import { UserLoginForm } from "./login"
import { UserSignupForm } from "./signup"

export function AuthForm() {
  const { theme } = useTheme()
  const router = useRouter()
  const pathname = router.state.location.pathname

  const isLogin = pathname === "/login"

  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-3xl bg-card/70 shadow-2xl shadow-primary/15 md:flex-row">
      {/* Left rail */}
      <div className="relative hidden h-full flex-col justify-between bg-gradient-to-br from-[#0f152a] via-[#101933] to-[#0b101f] p-10 md:flex md:w-5/12">
        <div className="absolute inset-0 opacity-70">
          <div className="bg-[radial-gradient(circle_at_20%_20%,rgba(18,100,159,0.35),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(227,198,122,0.24),transparent_30%)] h-full w-full" />
        </div>
        <div className="relative z-10 flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.15em] text-secondary-foreground/80">
          <img src="/images/badge.svg" alt="Litestar badge" className="h-9 w-9 drop-shadow-[0_8px_18px_rgba(0,0,0,0.4)]" />
          <span>Litestar fullstack</span>
        </div>
        <div className="relative z-10 space-y-6 text-foreground">
          <h2 className="font-['Space_Grotesk'] text-3xl font-semibold leading-tight">Typed APIs. Modern SPA. Ready-to-run jobs.</h2>
          <p className="text-muted-foreground">
            This reference app shows how Litestar, SAQ, and Vite fit together—JWT auth, OAuth, background workers, and a polished UI you can lift straight into production.
          </p>
          <div className="grid gap-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-secondary" />
              OpenAPI → SDK sync built-in
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary" />
              Granian + uvloop ready deploy
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-accent" />
              Background tasks powered by SAQ
            </div>
          </div>
        </div>
        <div className="relative z-10 text-xs text-muted-foreground">Secure by default · Structured logging · Tailored for teams</div>
      </div>

      {/* Form area */}
      <div className="flex h-full w-full items-center justify-center bg-card/60 p-6 backdrop-blur md:w-7/12 md:p-10">
        <div className="mx-auto flex w-full max-w-md flex-col gap-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-secondary-foreground/80">{isLogin ? "Welcome back" : "Create account"}</p>
              <h1 className="font-['Space_Grotesk'] text-2xl font-semibold text-foreground">{isLogin ? "Sign in to continue" : "Join the Litestar workspace"}</h1>
            </div>
            <Link to="/">
              <img src={theme === "dark" ? "/images/logo-light.svg" : "/images/logo-dark.svg"} alt="Litestar Logo" className="h-10 drop-shadow-[0_8px_20px_rgba(0,0,0,0.35)]" />
            </Link>
          </div>

          <div className="rounded-2xl border border-border/35 bg-card/85 p-6 shadow-lg shadow-primary/10 backdrop-blur-sm">{isLogin ? <UserLoginForm /> : <UserSignupForm />}</div>

          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{isLogin ? "Need an account?" : "Already have an account?"}</span>
            <Button asChild variant="secondary" size="sm" className="h-8 px-3 font-semibold shadow-sm">
              <Link to={isLogin ? "/signup" : "/login"}>{isLogin ? "Create one" : "Sign in"}</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
