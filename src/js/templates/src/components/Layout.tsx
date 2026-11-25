import { Body, Container, Head, Html, Preview, Section } from "@react-email/components"
import type { ReactNode } from "react"
import { emailTheme } from "../lib/theme"
import { Footer } from "./Footer"
import { Header } from "./Header"

interface LayoutProps {
  preview: string
  appName: string
  children: ReactNode
}

const bodyStyle = {
  backgroundColor: emailTheme.colors.bodyBg,
  fontFamily: emailTheme.fonts.primary,
  lineHeight: emailTheme.lineHeight,
  color: emailTheme.colors.textPrimary,
  padding: emailTheme.spacing.bodyPadding,
}

const containerStyle = {
  maxWidth: "600px",
  margin: "0 auto",
  backgroundColor: emailTheme.colors.containerBg,
  borderRadius: emailTheme.radius.container,
  overflow: "hidden" as const,
  border: `1px solid ${emailTheme.colors.border}`,
  boxShadow: emailTheme.shadows.container,
}

const contentStyle = {
  padding: emailTheme.spacing.containerPadding,
}

export const Layout = ({ preview, appName, children }: Readonly<LayoutProps>) => {
  return (
    <Html lang="en">
      <Head />
      <Preview>{preview}</Preview>
      <Body style={bodyStyle}>
        <Container style={containerStyle}>
          <Header appName={appName} />
          <Section style={contentStyle}>{children}</Section>
          <Footer appName={appName} />
        </Container>
      </Body>
    </Html>
  )
}
