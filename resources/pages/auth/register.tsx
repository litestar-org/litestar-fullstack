import React from "react"
import { GuestLayout } from "@/layouts/guest-layout"
import { InputError } from "@/components/input-error"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Head, Link, router, usePage } from "@inertiajs/react"
import { Checkbox } from "@/components/ui/checkbox"
import { route } from "litestar-vite-plugin/inertia-helpers"
import { z } from "zod"
import { useForm } from "react-hook-form"
import { FlashMessages } from "@/types"
import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { getServerSideErrors } from "@/lib/utils"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

const formSchema = z
  .object({
    name: z.string().min(3),
    email: z.string().email({ message: "Please enter a valid email address" }),
    password: z.string().min(8, {
      message: "Password must be at least 8 characters.",
    }),
    password_confirmation: z.string(),
    terms: z.literal(true),
  })
  .superRefine(({ password_confirmation, password }, ctx) => {
    if (password_confirmation !== password) {
      ctx.addIssue({
        code: "custom",
        message: "The passwords did not match",
        path: ["password_confirmation"],
      })
    }
  })
type FormProps = z.infer<typeof formSchema>
export default function Register() {
  const {
    hasTermsAndPrivacyPolicyFeature,
    flash,
    errors: serverSideErrors,
  } = usePage<{
    content: {
      status_code: number
      message: string
    }
    canResetPassword: boolean
    flash: FlashMessages
    hasTermsAndPrivacyPolicyFeature: boolean
  }>().props
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const form = useForm<
    FormProps & { password_confirmation: string; terms: boolean }
  >({
    resolver: zodResolver(formSchema),
  })

  const errors = {
    ...getServerSideErrors(serverSideErrors),
    ...form.formState.errors,
  }

  async function onSubmit(values: FormProps) {
    try {
      setIsLoading(true)
      router.post(route("register"), values, {
        onError: (err) => {
          console.log(err)
          if ("email" in err && typeof err.email === "string") {
            form.setError("root", { message: err.email })
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
      <Head title="Create a Fullstack Account" />
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2 text-center">
            {flash?.error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{flash.error.join("\n")}</AlertDescription>
              </Alert>
            )}
          </div>
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    autoComplete="name"
                    autoCorrect="off"
                    autoFocus
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
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
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
              <FormItem className="mt-4">
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    autoCapitalize="none"
                    autoCorrect="off"
                    autoComplete="password"
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
            name="password_confirmation"
            render={({ field }) => (
              <FormItem className="mt-4">
                <FormLabel>Confirm Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    autoCapitalize="none"
                    autoCorrect="off"
                    autoComplete="password_confirmation"
                    {...field}
                    disabled={isLoading}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {hasTermsAndPrivacyPolicyFeature && (
            <div>
              <FormField
                control={form.control}
                name="terms"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <div className="mt-2 flex items-center space-x-2">
                        <Checkbox
                          id="terms"
                          name="terms"
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                        <Label htmlFor="terms">Terms</Label>
                        <div className="ml-2">
                          I agree to the{" "}
                          <Link
                            target="_blank"
                            href={route("terms-of-service")}
                            className="text-sm text-muted-foreground hover:text-primary"
                          >
                            terms of service
                          </Link>{" "}
                          and{" "}
                          <Link
                            target="_blank"
                            href={route("privacy-policy")}
                            className="text-sm text-muted-foreground hover:text-primary"
                          >
                            privacy policy
                          </Link>
                        </div>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}
          <div className="mt-4 flex items-center justify-end">
            <Link
              href={route("login")}
              className="w-50 text-sm text-muted-foreground hover:text-primary"
            >
              Already registered?
            </Link>
            <Button
              type="submit"
              className="w-full text-base"
              disabled={isLoading}
            >
              Register
            </Button>
          </div>
        </form>
      </Form>
    </>
  )
}

Register.layout = (page: React.ReactNode) => {
  return (
    <GuestLayout
      header="Register"
      description="Create a Fullstack Account"
      children={page}
    />
  )
}
