import { Head, Link } from "@inertiajs/react"
import { AppLayout } from "@/layouts/app-layout"
import { Header } from "@/components/header"
import { Container } from "@/components/container"
import { Icons } from "@/components/icons"

import { BeakerIcon } from "lucide-react"
import { GuestLayout } from "@/layouts/guest-layout"
import { Logo } from "@/components/logo"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"
export default function Home() {
  return (
    <>
      <Head title="Welcome to Litestar" />
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
      <Container className="pb-16">
        <Link
          href={route("login")}
          className={cn(
            buttonVariants({ variant: "ghost" }),
            "absolute right-4 top-4 md:right-8 md:top-8"
          )}
        >
          Already have an account?
        </Link>
        <div className="p-4 sm:p-20">
          <Logo className="" />
          <div className="max-w-2xl">
            <div className="text-center mt-4 text-muted-foreground sm:mt-6 sm:text-lg">
              A reference application from the{" "}
              <a
                href="https://litestar.dev"
                target="_blank"
                className="text-foreground font-semibold"
              >
                Litestar
              </a>{" "}
              team
            </div>
          </div>

          <div className="mt-16 grid gap-4 xl:grid-cols-2">
            <div className="rounded-xl border bg-secondary/20 p-8">
              <a
                href="https://github.com/litestar-org/litestar-fullstack"
                className="flex items-center gap-x-2 font-semibold text-primary"
                target="_blank"
              >
                <Icons.gitHub className="size-8 stroke-1" />
                Litestar
              </a>
              <p className="mt-5 text-muted-foreground">
                This project is developed by{" "}
                <a
                  href="https://litestar.dev"
                  target="_blank"
                  className="text-foreground font-semibold"
                >
                  Litestar
                </a>
                , if you want to contribute to this project, please visit the{" "}
                <a
                  href="https://github.com/litestar-org/litestar-fullstack"
                  target="_blank"
                  className="text-foreground font-semibold"
                >
                  Github Repository
                </a>
                .
              </p>
            </div>
            <div className="rounded-xl border bg-secondary/20 p-8">
              <a
                href="https://inertiajs.com/"
                className="flex items-center gap-x-2 font-semibold text-primary"
                target="_blank"
              >
                <Icons.inertia className="size-8 stroke-1" />
                Inertia
              </a>
              <p className="mt-5 text-muted-foreground">
                Create modern single-page React, Vue, and Svelte apps using
                classic server-side routing. Works with any backend.
              </p>
            </div>

            <div className="rounded-xl border bg-secondary/20 p-8">
              <a
                href="https://docs.advanced-alchemy.litestar.dev/latest/"
                className="flex items-center gap-x-2 font-semibold text-primary"
                target="_blank"
              >
                <BeakerIcon className="size-8" />
                Advanced Alchemy
              </a>
              <p className="mt-5 text-muted-foreground">
                A carefully crafted, thoroughly tested, optimized companion
                library for SQLAlchemy
              </p>
            </div>
            <div className="rounded-xl border bg-secondary/20 p-8">
              <a
                href="https://react.dev/"
                className="flex items-center gap-x-2 font-semibold text-primary"
                target="_blank"
              >
                <Icons.react className="size-8" />
                React Template
              </a>
              <p className="mt-5 text-muted-foreground">
                Explore the next.js templates from web apps to design systems,
                all here.
              </p>
            </div>
          </div>
        </div>
        <p className="px-16 text-center text-sm text-muted-foreground">
          To enter this site, you must agree to our{" "}
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
      </Container>
    </>
  )
}

Home.layout = (page: any) => <GuestLayout children={page} />
