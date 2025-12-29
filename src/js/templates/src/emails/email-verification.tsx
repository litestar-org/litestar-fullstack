/**
 * Email Verification Template
 *
 * Placeholders:
 * - {{APP_NAME}} - Application name
 * - {{USER_NAME}} - User's display name
 * - {{VERIFICATION_URL}} - Email verification link
 * - {{EXPIRES_HOURS}} - Token expiration time in hours
 */

import { Heading, Text } from "@react-email/components"
import { Button, Layout } from "../components"

export default function EmailVerification() {
  return (
    <Layout
      preview="Verify your email address"
      appName="{{APP_NAME}}"
    >
      <Heading
        style={{
          margin: "0 0 16px 0",
          fontSize: "20px",
          fontWeight: 600,
          color: "#202235",
        }}
      >
        Verify your email address
      </Heading>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#5f6368",
          fontSize: "14px",
        }}
      >
        Hi {"{{USER_NAME}}"},
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          color: "#5f6368",
          fontSize: "14px",
        }}
      >
        Thank you for signing up for {"{{APP_NAME}}"}. Please verify your
        email address by clicking the button below:
      </Text>

      <div style={{ textAlign: "center" as const, margin: "32px 0" }}>
        <Button href="{{VERIFICATION_URL}}">Verify Email Address</Button>
      </div>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#5f6368",
          fontSize: "14px",
        }}
      >
        Or copy and paste this link into your browser:
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          padding: "12px 16px",
          backgroundColor: "#f8f9fa",
          borderRadius: "6px",
          fontSize: "12px",
          color: "#202235",
          wordBreak: "break-all" as const,
        }}
      >
        {"{{VERIFICATION_URL}}"}
      </Text>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#9aa0a6",
          fontSize: "13px",
        }}
      >
        This link will expire in {"{{EXPIRES_HOURS}}"} hours.
      </Text>

      <Text
        style={{
          margin: "24px 0 0 0",
          color: "#9aa0a6",
          fontSize: "13px",
        }}
      >
        If you didn't create an account with {"{{APP_NAME}}"}, you can safely
        ignore this email.
      </Text>
    </Layout>
  )
}
