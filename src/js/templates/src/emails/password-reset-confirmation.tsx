/**
 * Password Reset Confirmation Email Template
 *
 * Placeholders:
 * - {{APP_NAME}} - Application name
 * - {{USER_NAME}} - User's display name
 * - {{LOGIN_URL}} - Login page URL
 */

import { Heading, Text } from "@react-email/components"
import { Button, Layout } from "../components"

export default function PasswordResetConfirmation() {
  return (
    <Layout
      preview="Your password has been reset"
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
        Password reset complete
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
          margin: "0 0 16px 0",
          color: "#5f6368",
          fontSize: "14px",
        }}
      >
        Your password for {"{{APP_NAME}}"} has been successfully reset.
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          color: "#5f6368",
          fontSize: "14px",
        }}
      >
        If you did not make this change, please contact support immediately.
      </Text>

      <div style={{ textAlign: "center" as const, margin: "32px 0" }}>
        <Button href="{{LOGIN_URL}}">Sign In</Button>
      </div>

      <Text
        style={{
          margin: "24px 0 0 0",
          color: "#9aa0a6",
          fontSize: "13px",
        }}
      >
        For security, avoid reusing old passwords and consider enabling
        multi-factor authentication.
      </Text>
    </Layout>
  )
}
