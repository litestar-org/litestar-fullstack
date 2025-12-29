/**
 * Welcome Email Template
 *
 * Placeholders:
 * - {{APP_NAME}} - Application name
 * - {{USER_NAME}} - User's display name
 * - {{LOGIN_URL}} - Login page URL
 */

import { Heading, Text } from "@react-email/components"
import { Button, Layout } from "../components"

export default function Welcome() {
  return (
    <Layout
      preview="Welcome to {{APP_NAME}}"
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
        Welcome to {"{{APP_NAME}}"}!
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
        Your email has been verified and your account is now fully activated.
        We're excited to have you on board!
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          color: "#5f6368",
          fontSize: "14px",
        }}
      >
        Here's what you can do next:
      </Text>

      <ul style={{ margin: "0 0 24px 0", paddingLeft: "20px", color: "#5f6368" }}>
        <li style={{ marginBottom: "8px", fontSize: "14px" }}>
          Complete your profile settings
        </li>
        <li style={{ marginBottom: "8px", fontSize: "14px" }}>
          Enable two-factor authentication for extra security
        </li>
        <li style={{ marginBottom: "8px", fontSize: "14px" }}>
          Create or join a team
        </li>
      </ul>

      <div style={{ textAlign: "center" as const, margin: "32px 0" }}>
        <Button href="{{LOGIN_URL}}">Get Started</Button>
      </div>

      <Text
        style={{
          margin: "24px 0 0 0",
          color: "#9aa0a6",
          fontSize: "13px",
        }}
      >
        If you have any questions, feel free to reach out to our support team.
      </Text>
    </Layout>
  )
}
