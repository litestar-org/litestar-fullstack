import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { AlertCircle, CheckCircle2, Eye, EyeOff } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"
import { AuthSplitLayout } from "@/components/auth/auth-hero-panel"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { PasswordStrength } from "@/components/ui/password-strength"
import { extractApiErrorMessage, isGenericRejection } from "@/lib/api-client"
import { localPasswordResetMutation } from "@/lib/generated/api/@tanstack/react-query.gen"
import { newPasswordSchema } from "@/lib/validation"

export const Route = createFileRoute("/_public/reset-password")({
  validateSearch: (search) =>
    z
      .object({
        token: z.string().optional(),
      })
      .parse(search),
  component: ResetPasswordPage,
})

const LOGIN_REDIRECT_DELAY_MS = 3000
const RESET_REJECTED_MESSAGE = "We couldn't reset your password. The link may have expired, or the password may be too common. Request a new link or choose a different password."

const resetPasswordSchema = z
  .object({
    password: newPasswordSchema,
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((passwords) => passwords.password === passwords.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  })

type ResetPasswordForm = z.infer<typeof resetPasswordSchema>

function ResetPasswordPage() {
  const navigate = useNavigate()
  const { token } = useSearch({ from: "/_public/reset-password" })
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)
  const [isConfirmPasswordVisible, setIsConfirmPasswordVisible] = useState(false)

  const form = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: "",
      confirmPassword: "",
    },
  })

  const password = form.watch("password")

  const {
    mutate: resetPassword,
    isPending,
    isSuccess,
  } = useMutation({
    ...localPasswordResetMutation(),
    onSuccess: () => {
      toast.success("Password reset successfully!")
    },
    onError: (error) => {
      toast.error(isGenericRejection(error) ? RESET_REJECTED_MESSAGE : extractApiErrorMessage(error, "Failed to reset password"))
    },
  })

  useEffect(() => {
    if (!isSuccess) {
      return
    }
    const redirectTimer = setTimeout(() => void navigate({ to: "/login" }), LOGIN_REDIRECT_DELAY_MS)
    return () => clearTimeout(redirectTimer)
  }, [isSuccess, navigate])

  const handleResetPassword = (passwords: ResetPasswordForm) => {
    if (!token) {
      toast.error("Reset token is missing")
      return
    }
    resetPassword({ body: { token, password: passwords.password } })
  }

  if (!token) {
    return (
      <AuthSplitLayout heroDescription="Secure password recovery for your account.">
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
      </AuthSplitLayout>
    )
  }

  if (isSuccess) {
    return (
      <AuthSplitLayout heroDescription="Secure password recovery for your account.">
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
      </AuthSplitLayout>
    )
  }

  return (
    <AuthSplitLayout heroDescription="Secure password recovery for your account.">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Reset your password</h1>
        <p className="mt-2 text-sm text-muted-foreground">Enter your new password below</p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleResetPassword)} className="space-y-4">
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>New Password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input type={isPasswordVisible ? "text" : "password"} placeholder="Enter new password" {...field} />
                    <Button type="button" variant="ghost" size="icon" className="absolute top-0 right-0 h-full px-3" onClick={() => setIsPasswordVisible(!isPasswordVisible)}>
                      {isPasswordVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
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
                    <Input type={isConfirmPasswordVisible ? "text" : "password"} placeholder="Confirm new password" {...field} />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute top-0 right-0 h-full px-3"
                      onClick={() => setIsConfirmPasswordVisible(!isConfirmPasswordVisible)}
                    >
                      {isConfirmPasswordVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
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
    </AuthSplitLayout>
  )
}
