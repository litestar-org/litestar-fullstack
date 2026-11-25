import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { GitHubSignInButton } from "@/components/auth/github-signin-button"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { PasswordStrength } from "@/components/ui/password-strength"
import { useAuthConfig } from "@/lib/api/hooks/auth"
import { extractApiErrorMessage } from "@/lib/api-client"
import { localRegisterMutation } from "@/lib/generated/api/@tanstack/react-query.gen"
import { DEFAULT_AUTH_REDIRECT } from "@/lib/redirect-utils"
import { newPasswordSchema } from "@/lib/validation"

const signupSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: newPasswordSchema,
    name: z.string().min(1, "Name is required"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((signup) => signup.password === signup.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  })

type SignupFormData = z.infer<typeof signupSchema>

interface UserSignupFormProps {
  redirectUrl?: string | null
}

export function UserSignupForm({ redirectUrl }: Readonly<UserSignupFormProps>) {
  const navigate = useNavigate()
  const { data: authConfig } = useAuthConfig()
  const registerMutation = useMutation(localRegisterMutation())

  const redirectTarget = redirectUrl || DEFAULT_AUTH_REDIRECT
  const isGithubEnabled = authConfig?.githubEnabled ?? false

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
  const password = form.watch("password")

  const handleSignup = async (signup: SignupFormData) => {
    try {
      await registerMutation.mutateAsync({
        body: {
          identifier: signup.email,
          password: signup.password,
          display_name: signup.name,
        },
      })
      const isVerificationRequired = authConfig?.emailVerificationRequired ?? true
      toast.success(isVerificationRequired ? "Account created! Please check your email to verify your account." : "Account created! You can sign in now.")
      void navigate({ to: "/login", search: redirectUrl ? { redirect: redirectUrl } : undefined })
    } catch (error) {
      toast.error(extractApiErrorMessage(error, "Signup failed"))
    }
  }

  return (
    <div>
      <div className="grid gap-6">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSignup)} className="grid gap-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter your name" autoCapitalize="none" autoComplete="name" autoCorrect="off" {...field} disabled={registerMutation.isPending} />
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
                    <Input
                      placeholder="name@example.com"
                      autoCapitalize="none"
                      autoComplete="email"
                      autoCorrect="off"
                      {...field}
                      type="email"
                      disabled={registerMutation.isPending}
                    />
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
                      placeholder="Create a password"
                      autoCapitalize="none"
                      autoComplete="new-password"
                      autoCorrect="off"
                      {...field}
                      type="password"
                      disabled={registerMutation.isPending}
                    />
                  </FormControl>
                  <PasswordStrength password={password} />
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
                      disabled={registerMutation.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="mt-2 w-full" disabled={registerMutation.isPending}>
              {registerMutation.isPending && <Icons.Spinner className="mr-2 h-4 w-4" />}
              Create Account
            </Button>
          </form>
        </Form>

        {isGithubEnabled && (
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
              <GitHubSignInButton variant="signup" className="w-full" authRedirect={redirectTarget} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
