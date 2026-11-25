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
import { emailStyles, emailTheme } from "../lib/theme"

const nextStepListStyle = {
  margin: "0 0 24px 0",
  paddingLeft: "20px",
  color: emailTheme.colors.textBody,
}

const nextStepStyle = {
  marginBottom: "8px",
  fontSize: "14px",
}

export default function Welcome() {
  return (
    <Layout preview="Welcome to {{APP_NAME}}" appName="{{APP_NAME}}">
      <Heading style={emailStyles.heading}>Welcome to {"{{APP_NAME}}"}!</Heading>

      <Text style={emailStyles.paragraph}>Hi {"{{USER_NAME}}"},</Text>

      <Text style={emailStyles.paragraph}>Your email has been verified and your account is now fully activated. We're excited to have you on board!</Text>

      <Text style={emailStyles.lastParagraph}>Here's what you can do next:</Text>

      <ul style={nextStepListStyle}>
        <li style={nextStepStyle}>Complete your profile settings</li>
        <li style={nextStepStyle}>Enable two-factor authentication or register a passkey for extra security</li>
        <li style={nextStepStyle}>Create or join a team</li>
      </ul>

      <div style={emailStyles.buttonRow}>
        <Button href="{{LOGIN_URL}}">Get Started</Button>
      </div>

      <Text style={emailStyles.closingNote}>If you have any questions, feel free to reach out to our support team.</Text>
    </Layout>
  )
}
