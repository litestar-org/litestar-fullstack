import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, CheckCircle2, Mail } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { AuthHeroPanel } from "@/components/auth/auth-hero-panel"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { forgotPassword } from "@/lib/generated/api"

export const Route = createFileRoute("/_public/forgot-password")({
  component: ForgotPasswordPage,
})

const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
})

type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>

function ForgotPasswordPage() {
  const [isSuccess, setIsSuccess] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState("")

  const form = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  })

  const { mutate: requestReset, isPending } = useMutation({
    mutationFn: async (data: ForgotPasswordForm) => {
      const response = await forgotPassword({
        body: { email: data.email },
      })

      if (response.error) {
        throw new Error((response.error as any).detail || "Failed to send reset email")
      }

      return response.data
    },
    onSuccess: (_, variables) => {
      setSubmittedEmail(variables.email)
      setIsSuccess(true)
      toast.success("Password reset email sent!")
    },
    onError: (error: Error) => {
      // Don't reveal if email exists or not for security
      if (error.message.includes("not found")) {
        setSubmittedEmail(form.getValues("email"))
        setIsSuccess(true)
        toast.success("If an account exists, a reset email has been sent")
      } else {
        toast.error(error.message || "Failed to send reset email")
      }
    },
  })

  const onSubmit = (data: ForgotPasswordForm) => {
    requestReset(data)
  }

  if (isSuccess) {
    return (
      <div className="relative flex min-h-screen w-full">
        <AuthHeroPanel showTestimonial={false} description="Secure password recovery for your account." />
        <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
                <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h1 className="text-2xl font-semibold tracking-tight">Check your email</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                We sent a reset link to <strong>{submittedEmail}</strong>
              </p>
            </div>
            <Alert>
              <Mail className="h-4 w-4" />
              <AlertDescription>Links expire in one hour. Check spam or request another email if needed.</AlertDescription>
            </Alert>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setIsSuccess(false)
                  form.reset()
                }}
              >
                Send another email
              </Button>
              <Button asChild variant="ghost" className="w-full">
                <Link to="/login">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to login
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative flex min-h-screen w-full">
      <AuthHeroPanel showTestimonial={false} description="Secure password recovery for your account." />
      <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-semibold tracking-tight">Forgot your password?</h1>
            <p className="mt-2 text-sm text-muted-foreground">Enter your email and we'll send you a reset link.</p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="you@example.com" autoComplete="email" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? "Sending..." : "Send reset email"}
              </Button>
            </form>
          </Form>

          <Button asChild variant="ghost" className="w-full">
            <Link to="/login">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to login
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
