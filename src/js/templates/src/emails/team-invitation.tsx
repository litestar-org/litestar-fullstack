/**
 * Team Invitation Email Template
 *
 * Placeholders:
 * - {{APP_NAME}} - Application name
 * - {{INVITER_NAME}} - Name of the person who sent the invitation
 * - {{TEAM_NAME}} - Name of the team
 * - {{INVITATION_URL}} - Team invitation link
 */

import { Heading, Text } from "@react-email/components"
import { Button, Layout } from "../components"

export default function TeamInvitation() {
  return (
    <Layout preview="You've been invited to join {{TEAM_NAME}}" appName="{{APP_NAME}}">
      <Heading
        style={{
          margin: "0 0 16px 0",
          fontSize: "20px",
          fontWeight: 600,
          color: "#f3f4f6",
        }}
      >
        You've been invited to join a team
      </Heading>

      <Text
        style={{
          margin: "0 0 16px 0",
          color: "#d1d5db",
          fontSize: "14px",
        }}
      >
        Hello,
      </Text>

      <Text
        style={{
          margin: "0 0 24px 0",
          color: "#d1d5db",
          fontSize: "14px",
        }}
      >
        {"{{INVITER_NAME}}"} has invited you to join the team <strong>{"{{TEAM_NAME}}"}</strong> on {"{{APP_NAME}}"}.
      </Text>

      <div
        style={{
          margin: "0 0 24px 0",
          padding: "16px",
          backgroundColor: "#1c2237",
          borderRadius: "8px",
          borderLeft: "4px solid #FFB000",
        }}
      >
        <Text
          style={{
            margin: "0",
            color: "#f3f4f6",
            fontSize: "14px",
            fontWeight: 500,
          }}
        >
          Team: {"{{TEAM_NAME}}"}
        </Text>
        <Text
          style={{
            margin: "8px 0 0 0",
            color: "#d1d5db",
            fontSize: "13px",
          }}
        >
          Invited by: {"{{INVITER_NAME}}"}
        </Text>
      </div>

      <div style={{ textAlign: "center" as const, margin: "32px 0" }}>
        <Button href="{{INVITATION_URL}}" variant="success">
          Accept Invitation
        </Button>
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
        {"{{INVITATION_URL}}"}
      </Text>

      <Text
        style={{
          margin: "24px 0 0 0",
          color: "#9ca3af",
          fontSize: "13px",
        }}
      >
        If you don't want to join this team, you can safely ignore this email.
      </Text>
    </Layout>
  )
}
