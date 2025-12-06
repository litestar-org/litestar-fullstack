import { GoogleSignInButton } from "@/components/auth/google-signin-button"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { accountRegister } from "@/lib/api/sdk.gen"
import { useAuthStore } from "@/lib/auth"
import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

const signupSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    name: z.string().min(1, "Name is required"),
    confirmPassword: z.string().min(8, "Password must be at least 8 characters"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  })

type SignupFormData = z.infer<typeof signupSchema>

export function UserSignupForm() {
  const navigate = useNavigate()
  const { isLoading } = useAuthStore()

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

  const onSubmit = async (data: SignupFormData) => {
    try {
      const response = await accountRegister({
        body: { email: data.email, password: data.password, name: data.name },
      })

      if (response.status === 201) {
        toast.success("Account created! Please check your email to verify your account.")
        navigate({ to: "/login" })
        return
      }

      toast.error(response.error?.detail || "Signup failed")
    } catch (error) {
      toast.error("An error occurred during signup")
    }
  }

  return (
    <div className="relative flex h-full flex-col items-center justify-center">
      <div className="w-full max-w-md px-8">
        <div className="mb-4">
          <p className="text-sm text-muted-foreground leading-relaxed">Create your account with name, email, and password.</p>
        </div>
        <div className="grid gap-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-3">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem className="space-y-2">
                      <FormLabel className="text-sm font-medium text-foreground">Name</FormLabel>
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
                    <FormItem className="space-y-2">
                      <FormLabel className="text-sm font-medium text-foreground">Email</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Enter your email address"
                          autoCapitalize="none"
                          autoComplete="email"
                          autoCorrect="off"
                          {...field}
                          type="email"
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
                          placeholder="Create a password"
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

                <FormField
                  control={form.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem className="space-y-2">
                      <FormLabel className="text-sm font-medium text-foreground">Confirm Password</FormLabel>
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
              </div>

              <Button
                disabled={isLoading}
                className="w-full h-11 text-base font-semibold shadow-md shadow-primary/20 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-primary/40 active:translate-y-0 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                Sign Up
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
            <GoogleSignInButton variant="signup" className="w-full" onSuccess={() => navigate({ to: "/home" })} />
          </div>
        </div>
      </div>
    </div>
  )
}
