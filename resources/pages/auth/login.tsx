import { zodResolver } from "@hookform/resolvers/zod"
import { Head, Link, router, usePage } from "@inertiajs/react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { GuestLayout } from "@/layouts/guest-layout"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { PropsWithoutRef, useEffect } from "react"
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

const formSchema = z.object({
  username: z.string().email("Please enter a valid email address."),
  password: z.string().min(1, "Please enter a valid password."),
  remember: z.boolean().default(false),
})

export default function Login() {
  const { message, canResetPassword, errors } = usePage<{
    content: {
      status_code: number
      message: string
    }
    canResetPassword: boolean
  }>().props
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      password: "",
      remember: false,
    },
  })

  // 2. Define a submit handler.
  function onSubmit(values: z.infer<typeof formSchema>) {
    router.post(route("login"), values, {
      onError: (err) => {
        console.log(err)
        if ("username" in err && typeof err.username === "string") {
          form.setError("root", { message: err.username })
        }
      },
    })
  }
  useEffect(() => {
    if (errors) {
      for (const [key, value] of Object.entries(errors)) {
        if (key.startsWith("root")) continue

        form.setError(key as any, {
          type: "submit",
          message: value,
        })
      }
    }
  }, [errors])
  return (
    <>
      <Head title="Log in" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2 text-center">
            {form.formState.errors.root && (
              <p className="text-sm font-medium text-destructive">
                {form.formState.errors.root.message}
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
                  <Input {...field} />
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
                  <Input {...field} type="password" />
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
            disabled={!form.formState.isValid}
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
