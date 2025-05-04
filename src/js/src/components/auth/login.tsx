import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/auth";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function UserLoginForm() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
    mode: "onBlur",
    reValidateMode: "onBlur",
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      // TODO: Fix/verify login
      await login(data.email, data.password);
      // navigate({ to: "/home" });
    } catch (error) {
      form.setError("root", {
        message: "Invalid credentials",
      });
    }
  };

  const onOAuthLogin = async () => {
    // TODO: Implement OAuth login
    console.log("OAuth login");
  };

  return (
    <div className="relative flex flex-col h-full justify-center items-center">
      <Button variant="link" className="absolute top-0 right-0 p-4 hover:cursor-pointer" onClick={() => navigate({ to: "/signup" })}>
        Need an account?
      </Button>

      <div className="w-full max-w-md px-8">
        <div className="flex flex-col mb-4 text-center">
          <h1 className="flex mx-auto text-2xl font-semibold tracking-tight">Login to Continue</h1>
          <p className="text-sm text-muted-foreground">Enter your credentials to get started!</p>
        </div>
        <div className="grid gap-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
              <div className="grid gap-2">
                <div className="grid gap-1 ">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="sr-only">Email</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter your email." autoCapitalize="none" autoComplete="email" autoCorrect="off" {...field} disabled={isLoading} />
                        </FormControl>{" "}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid gap-1  ">
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="sr-only">Password</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Enter your current password."
                            type="password"
                            autoCapitalize="none"
                            autoCorrect="off"
                            autoComplete="current-password"
                            {...field}
                            disabled={isLoading}
                          />
                        </FormControl>{" "}
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <Button disabled={isLoading} className="hover:cursor-pointer">
                  Sign In
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
          <Button variant="outline" disabled={isLoading} className="hover:cursor-pointer" onClick={onOAuthLogin}>
            {isLoading ? (
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-b-2 border-current" />
            ) : (
              <img src={"images/google.svg"} alt="Litestar Logo" className="h-5 mr-2" />
            )}
            Sign in with Google
          </Button>
        </div>
      </div>
    </div>
  );
}
