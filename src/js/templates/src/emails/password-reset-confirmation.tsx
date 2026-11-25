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
import { emailStyles } from "../lib/theme"

export default function PasswordResetConfirmation() {
  return (
    <Layout preview="Your password has been reset" appName="{{APP_NAME}}">
      <Heading style={emailStyles.heading}>Password reset complete</Heading>

      <Text style={emailStyles.paragraph}>Hi {"{{USER_NAME}}"},</Text>

      <Text style={emailStyles.paragraph}>Your password for {"{{APP_NAME}}"} has been successfully reset.</Text>

      <Text style={emailStyles.lastParagraph}>If you did not make this change, please contact support immediately.</Text>

      <div style={emailStyles.buttonRow}>
        <Button href="{{LOGIN_URL}}">Sign In</Button>
      </div>

      <Text style={emailStyles.closingNote}>For security, avoid reusing old passwords and consider enabling multi-factor authentication or adding a passkey.</Text>
    </Layout>
  )
}
