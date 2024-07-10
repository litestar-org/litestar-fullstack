import { GuestLayout } from "@/layouts/guest-layout"
import { Button } from "@/components/ui/button"
import { Head, Link, useForm } from "@inertiajs/react"

export default function VerifyEmail({ status }: { status?: any }) {
  const { post, processing } = useForm()

  const submit = (e: { preventDefault: () => void }) => {
    e.preventDefault()

    post("/email/verification-notification")
  }
  return (
    <>
      <Head title="Email Verification" />
      {status === "verification-link-sent" && (
        <div className="mb-4 text-sm font-medium text-green-600">
          A new verification link has been sent to the email address you
          provided during registration.
        </div>
      )}

      <form onSubmit={submit}>
        <div className="mt-4 flex items-center justify-between">
          <Button disabled={processing} type="submit">
            Resend Verification Email
          </Button>
          <Link
            href={"/logout"}
            method="post"
            as="button"
            className="text-sm text-muted-foreground underline hover:text-foreground"
          >
            Log Out
          </Link>
        </div>
      </form>
    </>
  )
}

VerifyEmail.layout = (page: any) => (
  <GuestLayout
    header="Verify email"
    description="
                Thanks for signing up! Before getting started, could you verify your email address by clicking on the
                link we just emailed to you? If you didn't receive the email, we will gladly send you another."
    children={page}
  />
)
