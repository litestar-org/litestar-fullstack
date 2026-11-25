import { zodResolver } from "@hookform/resolvers/zod"
import { browserSupportsWebAuthn } from "@simplewebauthn/browser"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { GitHubSignInButton } from "@/components/auth/github-signin-button"
import { PasskeySignInButton } from "@/components/auth/passkey-signin-button"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useAuthConfig } from "@/lib/api/hooks/auth"
import { useAuthStore } from "@/lib/auth"
import { DEFAULT_AUTH_REDIRECT } from "@/lib/redirect-utils"
import { type LoginFormData, loginFormSchema } from "@/lib/validation"

interface UserLoginFormProps {
  redirectUrl?: string | null
}

export function UserLoginForm({ redirectUrl }: Readonly<UserLoginFormProps>) {
  const navigate = useNavigate()
  const { login, isLoading } = useAuthStore()
  const { data: authConfig } = useAuthConfig()

  const isGithubEnabled = authConfig?.githubEnabled ?? false
  const canUsePasskeys = (authConfig?.passkeysEnabled ?? false) && browserSupportsWebAuthn()
  const hasAlternativeMethods = isGithubEnabled || canUsePasskeys

  const redirectTarget = redirectUrl || DEFAULT_AUTH_REDIRECT

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: {
      username: "",
      password: "",
    },
    mode: "onBlur",
    reValidateMode: "onBlur",
  })

  const handleLogin = async (credentials: LoginFormData) => {
    const { mfaRequired, authenticated } = await login(credentials.username, credentials.password)
    if (mfaRequired) {
      void navigate({ to: "/mfa-challenge", search: { redirect: redirectTarget } })
      return
    }
    if (authenticated) {
      void navigate({ to: redirectTarget })
    }
  }

  return (
    <div>
      <div className="grid gap-6">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleLogin)} className="grid gap-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="name@example.com" autoCapitalize="none" autoComplete="email" autoCorrect="off" {...field} disabled={isLoading} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter your password"
                      type="password"
                      autoCapitalize="none"
                      autoCorrect="off"
                      autoComplete="current-password"
                      {...field}
                      disabled={isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="mt-2 w-full" disabled={isLoading}>
              {isLoading && <Icons.Spinner className="mr-2 h-4 w-4" />}
              Sign In
            </Button>
          </form>
        </Form>

        {hasAlternativeMethods && (
          <>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>
            <div className="grid gap-2">
              {canUsePasskeys && <PasskeySignInButton authRedirect={redirectTarget} className="w-full" />}
              {isGithubEnabled && <GitHubSignInButton variant="signin" className="w-full" authRedirect={redirectTarget} />}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
