import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { AlertCircle, CheckCircle2, Eye, EyeOff } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { AuthHeroPanel } from "@/components/auth/auth-hero-panel"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { PasswordStrength } from "@/components/ui/password-strength"
import { validatePassword } from "@/hooks/use-validation"
import { resetPassword } from "@/lib/generated/api"

export const Route = createFileRoute("/_public/reset-password")({
  validateSearch: (search) =>
    z
      .object({
        token: z.string().optional(),
      })
      .parse(search),
  component: ResetPasswordPage,
})

const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(1, "Password is required")
      .superRefine((value, ctx) => {
        const error = validatePassword(value)
        if (error) {
          ctx.addIssue({ code: z.ZodIssueCode.custom, message: error })
        }
      }),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  })

type ResetPasswordForm = z.infer<typeof resetPasswordSchema>

function ResetPasswordPage() {
  const navigate = useNavigate()
  const searchParams = useSearch({ from: "/_public/reset-password" })
  const token = searchParams.token
  const [isSuccess, setIsSuccess] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const form = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: "",
      confirmPassword: "",
    },
  })

  const password = form.watch("password")

  const { mutate: doResetPassword, isPending } = useMutation({
    mutationFn: async (data: ResetPasswordForm) => {
      if (!token) {
        throw new Error("Reset token is missing")
      }

      const response = await resetPassword({
        body: {
          token,
          password: data.password,
          password_confirm: data.confirmPassword,
        },
      })

      if (response.error) {
        throw new Error((response.error as any).detail || "Failed to reset password")
      }

      return response.data
    },
    onSuccess: () => {
      setIsSuccess(true)
      toast.success("Password reset successfully!")
      setTimeout(() => {
        navigate({ to: "/login" })
      }, 3000)
    },
    onError: (error: Error) => {
      if (error.message.includes("expired") || error.message.includes("invalid")) {
        toast.error("This reset link has expired or is invalid. Please request a new one.")
      } else {
        toast.error(error.message || "Failed to reset password")
      }
    },
  })

  const onSubmit = (data: ResetPasswordForm) => {
    doResetPassword(data)
  }

  if (!token) {
    return (
      <div className="relative flex min-h-screen w-full">
        <AuthHeroPanel showTestimonial={false} description="Secure password recovery for your account." />
        <div className="flex flex-1 flex-col items-center justify-center bg-brand-gray-light px-4 py-12 dark:bg-background">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-semibold tracking-tight">Invalid Reset Link</h1>
              <p className="mt-2 text-sm text-muted-foreground">This password reset link is invalid or incomplete.</p>
            </div>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>Please request a new password reset link.</AlertDescription>
            </Alert>
            <Button className="w-full" onClick={() => navigate({ to: "/forgot-password" })}>
              Request new reset link
            </Button>
          </div>
        </div>
      </div>
    )
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
              <h1 className="text-2xl font-semibold tracking-tight">Password Reset Successfully</h1>
              <p className="mt-2 text-sm text-muted-foreground">Your password has been reset. Redirecting to login...</p>
            </div>
            <Button className="w-full" onClick={() => navigate({ to: "/login" })}>
              Go to login
            </Button>
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
            <h1 className="text-2xl font-semibold tracking-tight">Reset your password</h1>
            <p className="mt-2 text-sm text-muted-foreground">Enter your new password below</p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>New Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input type={showPassword ? "text" : "password"} placeholder="Enter new password" {...field} />
                        <Button type="button" variant="ghost" size="icon" className="absolute top-0 right-0 h-full px-3" onClick={() => setShowPassword(!showPassword)}>
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </FormControl>
                    {password && <PasswordStrength password={password} className="pt-2" />}
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
                      <div className="relative">
                        <Input type={showConfirmPassword ? "text" : "password"} placeholder="Confirm new password" {...field} />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="absolute top-0 right-0 h-full px-3"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        >
                          {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? "Resetting..." : "Reset password"}
              </Button>
            </form>
          </Form>
        </div>
      </div>
    </div>
  )
}
