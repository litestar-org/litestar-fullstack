import { zodResolver } from "@hookform/resolvers/zod"
import { Head, Link, router, usePage } from "@inertiajs/react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { GuestLayout } from "@/layouts/guest-layout"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { useState } from "react"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { FlashMessages } from "@/types"

const formSchema = z.object({
  username: z.string().min(1, {
    message: "Username is required.",
  }),
  password: z.string().min(1, "Please enter a valid password."),
  remember: z.boolean().default(false),
})

export default function Login() {
  const { message, canResetPassword, errors, flash } = usePage<{
    content: {
      status_code: number
      message: string
    }
    canResetPassword: boolean
    flash: FlashMessages
  }>().props
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      password: "",
      remember: false,
    },
  })

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      setIsLoading(true)
      router.post(route("login"), values, {
        onError: (err) => {
          console.log(err)
          if ("username" in err && typeof err.username === "string") {
            form.setError("root", { message: err.username })
          }
        },
      })
    } catch (error: any) {
      console.log(error)
    } finally {
      setIsLoading(false)
    }
  }
  return (
    <>
      <Head title="Log in" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2 text-center">
            {flash?.error && (
              <p className="text-sm font-medium text-destructive">
                {flash.error.join("\n")}
              </p>
            )}
          </div>
          <FormField
            control={form.control}
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    autoCapitalize="none"
                    autoComplete="username"
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
              <FormItem className="mt-4">
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input
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

          <FormField
            control={form.control}
            name="remember"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <div className="mt-2 flex items-center space-x-2">
                    <Checkbox
                      id="remember-me"
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                    <Label htmlFor="remember-me">Remember me</Label>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className="w-full text-base"
            disabled={isLoading}
          >
            Sign in
          </Button>
          {canResetPassword && (
            <p className="text-center text-sm text-muted-foreground">
              <span className="">Forgot your password?</span>
              <Link
                href={route("reset-password.show")}
                className=" text-primary hover:underline"
              >
                Sign up
              </Link>
            </p>
          )}
          <p className="text-center text-sm text-muted-foreground">
            <span className="">Don't have an account?</span>
            <Link
              href={route("register")}
              className=" text-primary hover:underline"
            >
              Sign up
            </Link>
          </p>
        </form>
      </Form>
    </>
  )
}

Login.layout = (page: React.ReactNode) => {
  return (
    <GuestLayout
      header="Login"
      description="Please enter your email and password to login."
      children={page}
    />
  )
}
