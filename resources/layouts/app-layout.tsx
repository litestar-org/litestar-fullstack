import { PropsWithChildren } from "react"
import Navbar from "@/layouts/partials/navbar"
import Footer from "@/layouts/partials/footer"
import { Toaster } from "@/components/ui/toaster"

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="min-h-svh bg-muted/20">
      <Toaster />
      <Navbar />
      <main>{children}</main>
      <Footer />
    </div>
  )
}
