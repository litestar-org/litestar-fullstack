import { PropsWithChildren, ReactNode } from "react"

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
