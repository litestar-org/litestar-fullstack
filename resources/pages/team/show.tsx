import { Head } from "@inertiajs/react"
import React from "react"
import { AppLayout } from "@/layouts/app-layout"
import { Header } from "@/components/header"
import { Container } from "@/components/container"

export default function TeamShow({ about }: { about: string }) {
  return (
    <>
      <Head title="Teams" />
      <Header title="Team Info" />
      <Container>
        {/* Your about page content goes here. */}
        <div className="text-lime-600 dark:text-lime-400">
          "resources/pages/team/show.tsx"
        </div>
      </Container>
    </>
  )
}

TeamShow.layout = (page: React.ReactNode) => <AppLayout children={page} />
