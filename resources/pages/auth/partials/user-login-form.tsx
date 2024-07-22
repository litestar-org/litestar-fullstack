import { zodResolver } from "@hookform/resolvers/zod"
import { router, usePage } from "@inertiajs/react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
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
import { FlashMessages } from "@/types"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import { Icons } from "@/components/icons"

interface UserLoginFormProps extends React.HTMLAttributes<HTMLDivElement> {}
const formSchema = z.object({
  username: z.string().min(1, {
    message: "Username is required.",
  }),
  password: z.string().min(1, "Please enter a valid password."),
  remember: z.boolean().default(false),
})

type FormProps = z.infer<typeof formSchema>

export default function UserLoginForm({
  className,
  ...props
}: UserLoginFormProps) {
  const { content, canResetPassword, errors, flash } = usePage<{
    content: {
      status_code: number
      message: string
    }
    flash: FlashMessages
  }>().props
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const form = useForm<FormProps>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  })

  async function onSubmit(values: FormProps) {
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
      toast(
        content?.message ??
          error.response?.data?.detail ??
          "There was an unexpected error logging in."
      )
    } finally {
      setIsLoading(false)
    }
  }
  return (
    <div className={cn("grid gap-6", className)} {...props}>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <div className="grid gap-2">
            {flash?.error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{flash.error.join("\n")}</AlertDescription>
              </Alert>
            )}

            <div className="grid gap-1">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="sr-only">Username</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your username."
                        autoCapitalize="none"
                        autoComplete="username"
                        autoCorrect="off"
                        {...field}
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
                  <FormItem className="mt-4">
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

            <div className="grid gap-1 mt-10">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading && <Icons.spinner />}
                Sign In
              </Button>
            </div>
          </div>
        </form>
      </Form>
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      <Button variant="outline" type="button" disabled={isLoading}>
        {isLoading ? (
          <Icons.spinner className="w-5 mr-2 h-5" />
        ) : (
          <Icons.gitHub className="w-5 mr-2 h-5" />
        )}{" "}
        Sign in with Github
      </Button>
      <Button variant="outline" type="button" disabled={isLoading}>
        {isLoading ? (
          <Icons.spinner className="w-5 mr-2 h-5" />
        ) : (
          <Icons.google className="w-5 mr-2 h-5" />
        )}{" "}
        Sign in with Google
      </Button>
    </div>
  )
}
