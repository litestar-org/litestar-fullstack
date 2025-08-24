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
import { GoogleSignInButton } from "@/components/auth/google-signin-button"

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
      <Button variant="link" className="absolute top-0 right-0 p-4 hover:cursor-pointer" onClick={() => navigate({ to: "/login" })}>
        Have an account?
      </Button>

      <div className="w-full max-w-md px-8">
        <div className="mb-4 flex flex-col text-center">
          <h1 className="mx-auto flex font-semibold text-2xl tracking-tight">Join Fullstack</h1>
          <p className="text-muted-foreground text-sm">Enter your information below to create an account!</p>
        </div>
        <div className="grid gap-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
              <div className="grid gap-2">
                <div className="grid gap-1">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="sr-only">Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter your name." autoCapitalize="none" autoComplete="name" autoCorrect="off" {...field} disabled={isLoading} />
                        </FormControl>{" "}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid gap-1">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="sr-only">Email</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Enter your email address."
                            autoCapitalize="none"
                            autoComplete="email"
                            autoCorrect="off"
                            {...field}
                            type="email"
                            disabled={isLoading}
                          />
                        </FormControl>{" "}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid gap-1">
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="sr-only">Password</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Create a password."
                            autoCapitalize="none"
                            autoComplete="new-password"
                            autoCorrect="off"
                            {...field}
                            type="password"
                            disabled={isLoading}
                          />
                        </FormControl>{" "}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid gap-1">
                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="sr-only">Confirm Password</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Confirm your password."
                            autoCapitalize="none"
                            autoComplete="new-password"
                            autoCorrect="off"
                            {...field}
                            type="password"
                            disabled={isLoading}
                          />
                        </FormControl>{" "}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <Button disabled={isLoading} className="hover:cursor-pointer">
                  Sign Up
                  {isLoading && <div className="ml-2 h-4 w-4 animate-spin rounded-full border-current border-b-2" />}
                </Button>
              </div>
            </form>
          </Form>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>
          <GoogleSignInButton 
            variant="signup" 
            className="w-full"
            onSuccess={() => navigate({ to: "/home" })}
          />
        </div>
      </div>
    </div>
  )
}
