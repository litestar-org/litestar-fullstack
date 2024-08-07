import { Head } from "@inertiajs/react"
import React from "react"
import { AppLayout } from "@/layouts/app-layout"
import { Header } from "@/components/header"
import { Container } from "@/components/container"

export default function About({ about }: { about: string }) {
  return (
    <>
      <Head title="About Us" />
      <Header title="About Us" />
      <Container>
        {/* Your about page content goes here. */}
        <p>hello world</p>
      </Container>
    </>
  )
}

About.layout = (page: React.ReactNode) => <AppLayout children={page} />
