import { useTheme } from "@/lib/theme-context";
import { useRouter } from "@tanstack/react-router";

import { UserLoginForm } from "./login";
import { UserSignupForm } from "./signup";

export function AuthForm() {
  const { theme } = useTheme();
  const router = useRouter();
  const pathname = router.state.location.pathname;

  const isLogin = pathname === "/login";

  return (
    <div className="flex flex-col md:flex-row h-full w-full">
      {/* Left Column - Hidden on mobile */}
      <div className="hidden md:flex relative md:w-1/2 h-full flex-col bg-muted p-10 dark:border-r">
        <div className="absolute inset-0 bg-background/20" />
        <div className="relative z-20 flex items-center text-lg font-medium">
          <div className="relative z-20 flex items-center text-lg font-medium">
            <img src={theme === "dark" ? "images/logo-light.svg" : "images/logo-dark.svg"} alt="Litestar Logo" className="h-8 mr-3" />
            Litestar Fullstack Application
          </div>
        </div>
        <div className="relative z-20 mt-auto">
          <blockquote className="space-y-2">
            <p className="text-lg">&ldquo;One site to rule them all.&rdquo;</p>
            <footer className="text-sm">Litestar Org</footer>
          </blockquote>
        </div>
      </div>

      {/* Right Column - Full width on mobile */}
      <div className="h-full w-full md:w-1/2 p-4 sm:p-6 md:p-8 flex items-center justify-center">
        <div className="h-full w-full mx-auto flex flex-col justify-center space-y-6">{isLogin ? <UserLoginForm /> : <UserSignupForm />}</div>
      </div>
    </div>
  );
}
