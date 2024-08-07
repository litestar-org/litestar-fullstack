import { useEffect } from "react"
import { GuestLayout } from "@/layouts/guest-layout"
import { InputError } from "@/components/input-error"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Head, useForm } from "@inertiajs/react"

interface ResetPasswordProps {
  token: string
  email: string
}

type InputTargetProps = { name: any; value: any }

export default function ResetPassword(args: ResetPasswordProps) {
  const { token, email } = args
  const { data, setData, post, processing, errors, reset } = useForm({
    token: token,
    email: email,
    password: "",
    password_confirmation: "",
  })

  useEffect(() => {
    return () => {
      reset("password", "password_confirmation")
    }
  }, [])

  const onChange = (event: { target: InputTargetProps }) => {
    setData(event.target.name, event.target.value)
  }

  const submit = (e: { preventDefault: () => void }) => {
    e.preventDefault()
    post("/reset-password")
  }

  return (
    <>
      <Head title="Reset Password" />

      <form onSubmit={submit}>
        <div>
          <Label htmlFor="email">Email</Label>

          <Input
            type="email"
            name="email"
            value={data.email}
            autoComplete="username"
            onChange={onChange}
          />

          <InputError message={errors.email} className="mt-2" />
        </div>

        <div className="mt-4">
          <Label htmlFor="password">Password</Label>

          <Input
            type="password"
            name="password"
            value={data.password}
            autoComplete="new-password"
            autoFocus
            onChange={onChange}
          />

          <InputError message={errors.password} className="mt-2" />
        </div>

        <div className="mt-4">
          <Label htmlFor="password_confirmation">Confirm Password</Label>

          <Input
            type="password"
            name="password_confirmation"
            value={data.password_confirmation}
            autoComplete="new-password"
            onChange={onChange}
          />

          <InputError message={errors.password_confirmation} className="mt-2" />
        </div>

        <div className="mt-4 flex items-center justify-end">
          <Button type="submit" className="ml-4" disabled={processing}>
            Reset Password
          </Button>
        </div>
      </form>
    </>
  )
}

ResetPassword.layout = (page: any) => <GuestLayout children={page} />
