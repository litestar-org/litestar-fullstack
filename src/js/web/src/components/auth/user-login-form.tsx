import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { GitHubSignInButton } from "@/components/auth/github-signin-button"
import { GoogleSignInButton } from "@/components/auth/google-signin-button"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useOAuthConfig } from "@/hooks/use-oauth-config"
import { useAuthStore } from "@/lib/auth"
import { type LoginFormData, loginFormSchema } from "@/lib/validation"

interface UserLoginFormProps extends React.HTMLAttributes<HTMLDivElement> {}

export function UserLoginForm({ className, ...props }: UserLoginFormProps) {
  const navigate = useNavigate()
  const { login, isLoading } = useAuthStore()
  const { data: oauthConfig } = useOAuthConfig()

  const googleOAuthEnabled = oauthConfig?.googleEnabled ?? false
  const githubOAuthEnabled = oauthConfig?.githubEnabled ?? false
  const hasOAuthProviders = googleOAuthEnabled || githubOAuthEnabled

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: {
      username: "",
      password: "",
    },
    mode: "onBlur",
    reValidateMode: "onBlur",
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      const result = await login(data.username, data.password)
      if (result.mfaRequired) {
        navigate({ to: "/mfa-challenge" })
        return
      }
      navigate({ to: "/home" })
    } catch (_error) {
      // Error is handled by useAuthStore
    }
  }

  return (
    <div className={className} {...props}>
      <div className="grid gap-6">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
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
              {isLoading && <Icons.spinner className="mr-2 h-4 w-4" />}
              Sign In
            </Button>
          </form>
        </Form>

        {hasOAuthProviders && (
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
              {githubOAuthEnabled && <GitHubSignInButton variant="signin" className="w-full" onSuccess={() => navigate({ to: "/home" })} />}
              {googleOAuthEnabled && <GoogleSignInButton variant="signin" className="w-full" onSuccess={() => navigate({ to: "/home" })} />}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
