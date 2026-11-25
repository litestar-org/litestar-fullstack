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
import { emailStyles, emailTheme } from "../lib/theme"

const invitationSummaryStyle = {
  margin: "0 0 24px 0",
  padding: "16px",
  backgroundColor: emailTheme.colors.codeBg,
  borderRadius: emailTheme.radius.code,
  borderLeft: `4px solid ${emailTheme.colors.brandGold}`,
}

const teamNameStyle = {
  margin: "0",
  color: emailTheme.colors.textHeading,
  fontSize: "14px",
  fontWeight: 500,
}

const inviterNameStyle = {
  margin: "8px 0 0 0",
  color: emailTheme.colors.textBody,
  fontSize: "13px",
}

export default function TeamInvitation() {
  return (
    <Layout preview="You've been invited to join {{TEAM_NAME}}" appName="{{APP_NAME}}">
      <Heading style={emailStyles.heading}>You've been invited to join a team</Heading>

      <Text style={emailStyles.paragraph}>Hello,</Text>

      <Text style={emailStyles.lastParagraph}>
        {"{{INVITER_NAME}}"} has invited you to join the team <strong>{"{{TEAM_NAME}}"}</strong> on {"{{APP_NAME}}"}.
      </Text>

      <div style={invitationSummaryStyle}>
        <Text style={teamNameStyle}>Team: {"{{TEAM_NAME}}"}</Text>
        <Text style={inviterNameStyle}>Invited by: {"{{INVITER_NAME}}"}</Text>
      </div>

      <div style={emailStyles.buttonRow}>
        <Button href="{{INVITATION_URL}}" variant="success">
          Accept Invitation
        </Button>
      </div>

      <Text style={emailStyles.paragraph}>Or copy and paste this link into your browser:</Text>

      <Text style={emailStyles.linkBox}>{"{{INVITATION_URL}}"}</Text>

      <Text style={emailStyles.closingNote}>If you don't want to join this team, you can safely ignore this email.</Text>
    </Layout>
  )
}
