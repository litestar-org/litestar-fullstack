/**
 * Password Reset Template
 *
 * Placeholders:
 * - {{APP_NAME}} - Application name
 * - {{USER_NAME}} - User's display name
 * - {{RESET_URL}} - Password reset link
 * - {{EXPIRES_HOURS}} - Token expiration time in hours
 */

import { Heading, Text } from "@react-email/components"
import { Button, Layout } from "../components"

export default function PasswordReset() {
  return (
    <Layout preview="Reset your password" appName="{{APP_NAME}}">
      <Heading
        style={{
          margin: "0 0 16px 0",
          fontSize: "20px",
          fontWeight: 600,
          color: "#f3f4f6",
        }}
      >
        Reset your password
      </Heading>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#d1d5db",
          fontSize: "14px",
        }}
      >
        Hi {"{{USER_NAME}}"},
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          color: "#d1d5db",
          fontSize: "14px",
        }}
      >
        We received a request to reset your password for your {"{{APP_NAME}}"} account. Click the button below to choose a new password:
      </Text>

      <div style={{ textAlign: "center" as const, margin: "32px 0" }}>
        <Button href="{{RESET_URL}}">Reset Password</Button>
      </div>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#d1d5db",
          fontSize: "14px",
        }}
      >
        Or copy and paste this link into your browser:
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          padding: "12px 16px",
          backgroundColor: "#1c2237",
          borderRadius: "6px",
          fontSize: "12px",
          color: "#FFB000",
          wordBreak: "break-all" as const,
        }}
      >
        {"{{RESET_URL}}"}
      </Text>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#9ca3af",
          fontSize: "13px",
        }}
      >
        This link will expire in {"{{EXPIRES_HOURS}}"} hours.
      </Text>

      <Text
        style={{
          margin: "24px 0 0 0",
          color: "#9ca3af",
          fontSize: "13px",
        }}
      >
        If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
      </Text>
    </Layout>
  )
}
