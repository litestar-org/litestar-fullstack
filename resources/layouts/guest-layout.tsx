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
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

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
    <div className="container relative  h-full flex-col items-center justify-center md:grid lg:max-w-none lg:grid-cols-2 lg:px-0">
      {children}
    </div>
  )
}
