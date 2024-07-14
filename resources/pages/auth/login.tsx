import React, { useEffect } from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { GuestLayout } from "@/layouts/guest-layout"
import { InputError } from "@/components/input-error"
import { Label } from "@/components/ui/label"
import { Button, buttonVariants } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Head, Link, useForm } from "@inertiajs/react"
import { route } from "litestar-vite-plugin/inertia-helpers"

interface LoginProps {
  content?: {
    status_code: number
    detail: string
  }
  canResetPassword: boolean
}

export default function Login(args: LoginProps) {
  const { content, canResetPassword } = args
  const { data, setData, post, processing, errors, reset } = useForm({
    username: "",
    password: "",
    remember: "",
  })

  useEffect(() => {
    return () => {
      reset("password")
    }
  }, [])

  const onChange = (event: { target: { name: any; value: any } }) => {
    setData(event.target.name, event.target.value)
  }

  const submit = (e: { preventDefault: () => void }) => {
    e.preventDefault()

    post(route("login"))
  }

  return (
    <>
      <Head title="Log in" />

      {content && (
        <div className="mb-4 text-sm font-medium text-red-600 dark:text-red-400">
          {content.detail}
        </div>
      )}

      <form onSubmit={submit} className="space-y-6">
        <div>
          <Label htmlFor="username">Email</Label>

          <Input
            type="text"
            name="username"
            value={data.username}
            className="mt-1"
            autoComplete="username"
            autoFocus
            onChange={onChange}
          />

          <InputError message={errors.username} className="mt-2" />
        </div>

        <div className="mt-4">
          <Label htmlFor="password">Password</Label>

          <Input
            type="password"
            name="password"
            value={data.password}
            className="mt-1"
            autoComplete="current-password"
            onChange={onChange}
          />

          <InputError message={errors.password} className="mt-2" />
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center">
            <Checkbox name="remember" onCheckedChange={(e) => e} />

            <span className="ml-2 text-sm text-muted-foreground select-none">
              Remember me
            </span>
          </label>
          {canResetPassword && (
            <Link
              href="/forgot-password"
              className="text-sm text-foreground hover:underline"
            >
              Forgot your password?
            </Link>
          )}
        </div>

        <div className="flex items-center justify-between">
          <Link
            href={route("register")}
            className={buttonVariants({ variant: "outline" })}
          >
            Register
          </Link>

          <Button disabled={processing} type="submit">
            Log in
          </Button>
        </div>
      </form>
    </>
  )
}

Login.layout = (page: React.ReactNode) => {
  return (
    <GuestLayout
      header="Login"
      description="Log in to your account."
      children={page}
    />
  )
}
