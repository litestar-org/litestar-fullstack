import { useTheme } from "@/lib/theme-context"
import { Link, useRouter } from "@tanstack/react-router"

import { UserLoginForm } from "./login"
import { UserSignupForm } from "./signup"

export function AuthForm() {
  const { theme } = useTheme()
  const router = useRouter()
  const pathname = router.state.location.pathname

  const isLogin = pathname === "/login"

  return (
    <div className="flex h-full w-full flex-col md:flex-row">
      {/* Left Column - Hidden on mobile */}
      <div className="relative hidden h-full flex-col bg-muted p-10 md:flex md:w-1/2 dark:border-r">
        <div className="absolute inset-0 bg-background/20" />
        <div className="relative z-20 flex items-center font-medium text-lg">
          {/* Navigates to `/landing` if user is not logged in */}
          <Link to="/">
            <div className="relative z-20 flex items-center font-medium text-lg">
              <img src={theme === "dark" ? "images/logo-light.svg" : "images/logo-dark.svg"} alt="Litestar Logo" className="mr-3 h-8" />
              Litestar Fullstack Application
            </div>
          </Link>
        </div>
        <div className="relative z-20 mt-auto">
          <blockquote className="space-y-2">
            {isLogin ? (
              <>
                <p className="text-lg">
                  &ldquo;This library has saved me countless hours of work and helped me deliver stunning designs to my clients faster than ever before.&rdquo;
                </p>
                <footer className="text-sm">Sofia Davis</footer>
              </>
            ) : (
              <>
                <p className="text-lg">
                  &ldquo;This library has saved me countless hours of assessment work and helped me identify the best databases for us to start our migration journey with.&rdquo;
                </p>
                <footer className="text-sm">A happy customer</footer>
              </>
            )}
          </blockquote>
        </div>
      </div>

      {/* Right Column - Full width on mobile */}
      <div className="flex h-full w-full items-center justify-center p-4 sm:p-6 md:w-1/2 md:p-8">
        <div className="mx-auto flex h-full w-full flex-col justify-center space-y-6">{isLogin ? <UserLoginForm /> : <UserSignupForm />}</div>
      </div>
    </div>
  )
}
