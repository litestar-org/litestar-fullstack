import { useRef } from "react"
import { InputError } from "@/components/input-error"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useForm } from "@inertiajs/react"
import { Transition } from "@headlessui/react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { route } from "litestar-vite-plugin/inertia-helpers"
import { toast } from "@/components/ui/use-toast"

export default function UpdatePasswordForm({
  className,
}: {
  className?: string
}) {
  const passwordInput = useRef<HTMLInputElement>(null)
  const currentPasswordInput = useRef<HTMLInputElement>(null)
  const {
    data,
    setData,
    patch,
    errors,
    reset,
    processing,
    recentlySuccessful,
  } = useForm({
    currentPassword: "",
    newPassword: "",
    passwordConfirmation: "",
  })

  const submit = (e: { preventDefault: () => void }) => {
    e.preventDefault()
    patch(route("password.update"), {
      preserveScroll: true,
      onSuccess: () => {
        toast({ description: "Your password has been updated." })
        reset()
      },
      onError: () => {
        if (errors.newPassword) {
          reset("newPassword", "passwordConfirmation")
          passwordInput.current?.focus()
        }

        if (errors.currentPassword) {
          reset("currentPassword")
          currentPasswordInput.current?.focus()
        }
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Update Password</CardTitle>
        <CardDescription>
          Ensure your account is using a long, random password to stay secure.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={submit} className="space-y-6">
          <div>
            <Label htmlFor="currentPassword">Current Password</Label>

            <Input
              id="currentPassword"
              ref={currentPasswordInput}
              value={data.currentPassword}
              className="mt-1"
              onChange={(e) => setData("currentPassword", e.target.value)}
              type="password"
              autoComplete="currentPassword"
              required
            />

            <InputError message={errors.currentPassword} className="mt-2" />
          </div>

          <div>
            <Label htmlFor="newPassword">New Password</Label>

            <Input
              id="newPassword"
              ref={passwordInput}
              value={data.newPassword}
              className="mt-1"
              onChange={(e) => setData("newPassword", e.target.value)}
              type="password"
              autoComplete="newPassword"
              required
            />

            <InputError message={errors.newPassword} className="mt-2" />
          </div>

          <div>
            <Label htmlFor="passwordConfirmation">Confirm Password</Label>

            <Input
              id="passwordConfirmation"
              value={data.passwordConfirmation}
              className="mt-1"
              onChange={(e) => setData("passwordConfirmation", e.target.value)}
              type="password"
              autoComplete="newPassword"
              required
            />

            <InputError
              message={errors.passwordConfirmation}
              className="mt-2"
            />
          </div>

          <div className="flex items-center gap-4">
            <Button disabled={processing}>Save</Button>

            <Transition
              show={recentlySuccessful}
              enterFrom="opacity-0"
              leaveTo="opacity-0"
              className="transition ease-in-out"
            >
              <p className="text-sm text-muted-foreground">Saved.</p>
            </Transition>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
