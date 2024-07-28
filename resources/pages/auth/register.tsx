import { Head, Link } from "@inertiajs/react"
import { GuestLayout } from "@/layouts/guest-layout"
import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Icons } from "@/components/icons"
import UserLoginForm from "./partials/user-login-form"
import UserRegistrationForm from "./partials/user-registration-form"

export default function Login() {
  return (
    <>
      <Head title="Register account" />
      <Link
        href={route("login")}
        className={cn(
          buttonVariants({ variant: "ghost" }),
          "absolute right-4 top-4 md:right-8 md:top-8"
        )}
      >
        Already have an account?
      </Link>
      <div className="relative hidden h-full flex-col  p-10 dark:border-r lg:flex">
        <div className="absolute inset-0 bg-none" />
        <Link href={route("home")}>
          <div className="relative z-20 flex items-center text-lg font-medium">
            <Icons.logo className="mr-2 h-6 w-6" />
            Litestar Fullstack Application
          </div>
        </Link>
        <div className="relative z-20 mt-auto"></div>
      </div>

      <div className="lg:p-8 sm:pt-5">
        <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
          <div className="flex flex-col space-y-2 text-center">
            <h1 className="flex mx-auto text-2xl font-semibold tracking-tight">
              <Icons.sparkle className="w-5 h-5 mr-3 " /> Signup to get started{" "}
            </h1>
            <p className="text-sm text-muted-foreground ">
              Create an account to continue.
            </p>
          </div>
          <UserRegistrationForm />
          <p className="px-8 text-center text-sm text-muted-foreground">
            By clicking continue, you agree to our{" "}
            <Link
              href={route("terms-of-service")}
              className="underline underline-offset-4 hover:text-primary"
            >
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link
              href={route("privacy-policy")}
              className="underline underline-offset-4 hover:text-primary"
            >
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      </div>
    </>
  )
}

Login.layout = (page: React.ReactNode) => {
  return <GuestLayout children={page} />
}
