import {
  Body,
  Container,
  Head,
  Html,
  Preview,
  Section,
} from "@react-email/components"
import type { ReactNode } from "react"
import { Footer } from "./Footer"
import { Header } from "./Header"

interface LayoutProps {
  preview: string
  appName: string
  children: ReactNode
}

export const Layout = ({ preview, appName, children }: LayoutProps) => {
  return (
    <Html lang="en">
      <Head />
      <Preview>{preview}</Preview>
      <Body style={main}>
        <Container style={container}>
          <Header appName={appName} />
          <Section style={content}>{children}</Section>
          <Footer appName={appName} />
        </Container>
      </Body>
    </Html>
  )
}

const main = {
  backgroundColor: "#DCDFE4",
  fontFamily:
    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif",
  lineHeight: "1.6",
  color: "#202235",
  padding: "40px 20px",
}

const container = {
  maxWidth: "600px",
  margin: "0 auto",
  backgroundColor: "#ffffff",
  borderRadius: "10px",
  overflow: "hidden" as const,
  border: "1px solid #DCDFE4",
  boxShadow: "0 8px 24px rgba(32, 34, 53, 0.08)",
}

const content = {
  padding: "36px 40px",
}
