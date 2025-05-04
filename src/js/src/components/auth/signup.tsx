import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { accountRegister } from "@/lib/api/sdk.gen"
import { useAuthStore } from "@/lib/auth"
import { zodResolver } from "@hookform/resolvers/zod"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
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
      // TODO: verify registration
      await accountRegister({
        body: { email: data.email, password: data.password, name: data.name },
      })
      // navigate({ to: "/login" });
    } catch (error) {
      form.setError("root", {
        message: "Signup failed",
      })
    }
  }

  const onOAuthSignup = async () => {
    // TODO: Implement OAuth login
    console.log("OAuth signup")
  }

  return (
    <div className="relative flex flex-col h-full justify-center items-center">
      <Button variant="link" className="absolute top-0 right-0 p-4 hover:cursor-pointer" onClick={() => navigate({ to: "/login" })}>
        Have an account?
      </Button>

      <div className="w-full max-w-md px-8">
        <div className="flex flex-col mb-4 text-center">
          <h1 className="flex mx-auto text-2xl font-semibold tracking-tight">Join Fullstack</h1>
          <p className="text-sm text-muted-foreground">Enter your information below to create an account!</p>
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
                  {isLoading && <div className="ml-2 h-4 w-4 animate-spin rounded-full border-b-2 border-current" />}
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
          <Button variant="outline" disabled={isLoading} className="hover:cursor-pointer" onClick={onOAuthSignup}>
            {isLoading ? (
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-b-2 border-current" />
            ) : (
              <img src={"images/google.svg"} alt="Litestar Logo" className="h-5 mr-2" />
            )}
            Sign up with Google
          </Button>
        </div>
      </div>
    </div>
  )
}
