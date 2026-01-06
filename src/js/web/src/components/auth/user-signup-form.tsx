import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { GitHubSignInButton } from "@/components/auth/github-signin-button"
import { GoogleSignInButton } from "@/components/auth/google-signin-button"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { PasswordStrength } from "@/components/ui/password-strength"
import { useOAuthConfig } from "@/hooks/use-oauth-config"
import { validatePassword } from "@/hooks/use-validation"
import { useAuthStore } from "@/lib/auth"
import { accountRegister } from "@/lib/generated/api"
import { DEFAULT_AUTH_REDIRECT } from "@/lib/redirect-utils"

const signupSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: z
      .string()
      .min(1, "Password is required")
      .superRefine((value, ctx) => {
        const error = validatePassword(value)
        if (error) {
          ctx.addIssue({ code: z.ZodIssueCode.custom, message: error })
        }
      }),
    name: z.string().min(1, "Name is required"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  })

type SignupFormData = z.infer<typeof signupSchema>

interface UserSignupFormProps extends React.HTMLAttributes<HTMLDivElement> {
  redirectUrl?: string | null
}

export function UserSignupForm({ className, redirectUrl, ...props }: UserSignupFormProps) {
  const navigate = useNavigate()
  const { isLoading } = useAuthStore()
  const { data: oauthConfig } = useOAuthConfig()
  const finalRedirect = redirectUrl || DEFAULT_AUTH_REDIRECT

  const googleOAuthEnabled = oauthConfig?.googleEnabled ?? false
  const githubOAuthEnabled = oauthConfig?.githubEnabled ?? false
  const hasOAuthProviders = googleOAuthEnabled || githubOAuthEnabled

  const form = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      email: "",
      password: "",
      name: "",
      confirmPassword: "",
    },
    mode: "onBlur",
    reValidateMode: "onBlur",
  })
  const passwordValue = form.watch("password")

  const onSubmit = async (data: SignupFormData) => {
    try {
      const response = await accountRegister({
        body: { email: data.email, password: data.password, name: data.name },
      })

      if (response.data) {
        toast.success("Account created! Please check your email to verify your account.")
        // Preserve redirect URL when navigating to login
        const loginSearch = redirectUrl ? { redirect: redirectUrl } : undefined
        navigate({ to: "/login", search: loginSearch })
        return
      }

      toast.error(response.error?.detail || "Signup failed")
    } catch (_error) {
      toast.error("An error occurred during signup")
    }
  }

  return (
    <div className={className} {...props}>
      <div className="grid gap-6">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter your name" autoCapitalize="none" autoComplete="name" autoCorrect="off" {...field} disabled={isLoading} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="name@example.com" autoCapitalize="none" autoComplete="email" autoCorrect="off" {...field} type="email" disabled={isLoading} />
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
                    <Input placeholder="Create a password" autoCapitalize="none" autoComplete="new-password" autoCorrect="off" {...field} type="password" disabled={isLoading} />
                  </FormControl>
                  <PasswordStrength password={passwordValue} />
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm Password</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Confirm your password"
                      autoCapitalize="none"
                      autoComplete="new-password"
                      autoCorrect="off"
                      {...field}
                      type="password"
                      disabled={isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="mt-2 w-full" disabled={isLoading}>
              {isLoading && <Icons.spinner className="mr-2 h-4 w-4" />}
              Create Account
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
              {githubOAuthEnabled && <GitHubSignInButton variant="signup" className="w-full" authRedirect={finalRedirect} onSuccess={() => navigate({ to: finalRedirect })} />}
              {googleOAuthEnabled && <GoogleSignInButton variant="signup" className="w-full" authRedirect={finalRedirect} onSuccess={() => navigate({ to: finalRedirect })} />}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
