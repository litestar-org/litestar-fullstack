import { Head } from "@inertiajs/react"
import React from "react"
import { AppLayout } from "@/layouts/app-layout"
import { Header } from "@/components/header"
import { Container } from "@/components/container"

export default function TeamList({ about }: { about: string }) {
  return (
    <>
      <Head title="Teams" />
      <Header title="All Teams" />
      <Container>
        {/* Your about page content goes here. */}
        <div className="text-lime-600 dark:text-lime-400">
          "resources/pages/team/list.tsx"
        </div>
      </Container>
    </>
  )
}

TeamList.layout = (page: React.ReactNode) => <AppLayout children={page} />
