import { PropsWithChildren } from "react"
import Navbar from "@/layouts/partials/navbar"
import Footer from "@/layouts/partials/footer"
import { Toaster } from "@/components/ui/toaster"

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="h-screen bg-muted/20">
      <Toaster />
      <Navbar />
      <main>
        <div className="mb-auto">{children}</div>
      </main>
      <Footer />
    </div>
  )
}
