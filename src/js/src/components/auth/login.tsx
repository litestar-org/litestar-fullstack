import { GoogleSignInButton } from "@/components/auth/google-signin-button"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useAuthStore } from "@/lib/auth"
import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { z } from "zod"

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

type LoginFormData = z.infer<typeof loginSchema>

export function UserLoginForm() {
  const navigate = useNavigate()
  const { login, isLoading } = useAuthStore()

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
    mode: "onBlur",
    reValidateMode: "onBlur",
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password)
      navigate({ to: "/home" })
    } catch (error) {
      // Error is handled by useAuthStore
    }
  }

  return (
    <div className="relative flex h-full flex-col items-center justify-center">
      <div className="w-full max-w-md px-8">
        <div className="mb-4">
          <p className="text-sm text-muted-foreground leading-relaxed">Use your email and password to sign in.</p>
        </div>
        <div className="grid gap-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-3">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem className="space-y-2">
                      <FormLabel className="text-sm font-medium text-foreground">Email</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Enter your email"
                          autoCapitalize="none"
                          autoComplete="email"
                          autoCorrect="off"
                          {...field}
                          disabled={isLoading}
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
                    <FormItem className="space-y-2">
                      <FormLabel className="text-sm font-medium text-foreground">Password</FormLabel>
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
              </div>

              <div className="flex items-center justify-between text-sm">
                <a href="/forgot-password" className="text-muted-foreground hover:text-primary">
                  Forgot password?
                </a>
              </div>

              <Button
                disabled={isLoading}
                className="w-full h-11 text-base font-semibold shadow-md shadow-primary/20 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-primary/40 active:translate-y-0 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                Sign In
                {isLoading && <div className="ml-2 h-4 w-4 animate-spin rounded-full border-current border-b-2" />}
              </Button>
            </form>
          </Form>
          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border/40" />
            </div>
            <div className="relative flex justify-center text-[11px] uppercase tracking-[0.16em]">
              <span className="relative z-10 rounded-full bg-card px-4 py-1 text-muted-foreground shadow-sm shadow-black/10">
                Or continue with
              </span>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <GoogleSignInButton variant="signin" className="w-full" onSuccess={() => navigate({ to: "/home" })} />
          </div>
        </div>
      </div>
    </div>
  )
}
