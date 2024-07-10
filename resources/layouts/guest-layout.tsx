import { PropsWithChildren, ReactNode } from "react"
import { Logo } from "@/components/logo"
import { Link } from "@inertiajs/react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { route } from "litestar-vite-plugin/inertia-helpers"

interface GuestLayoutProps {
  header?: string | null
  description?: string | ReactNode | null
}

export function GuestLayout({
  description = null,
  header = null,
  children,
}: PropsWithChildren<GuestLayoutProps>) {
  return (
    <div className="flex min-h-screen flex-col items-center pt-6 sm:justify-center sm:pt-0">
      <Link href={route("home")}>
        <Logo className="mx-auto h-16 w-16 fill-foreground" />
      </Link>

      <div className="mt-10 w-full max-w-lg">
        <Card className="rounded-none border-l-transparent border-r-transparent shadow-none sm:rounded-lg sm:border-l-border sm:border-r-border sm:shadow-sm lg:rounded-xl ">
          <CardHeader className="flex-row justify-between">
            <div>
              <CardTitle>{header}</CardTitle>
              <CardDescription className="mt-2">{description}</CardDescription>
            </div>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
      </div>
    </div>
  )
}
