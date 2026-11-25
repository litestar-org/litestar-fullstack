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
import { emailStyles } from "../lib/theme"

export default function PasswordReset() {
  return (
    <Layout preview="Reset your password" appName="{{APP_NAME}}">
      <Heading style={emailStyles.heading}>Reset your password</Heading>

      <Text style={emailStyles.paragraph}>Hi {"{{USER_NAME}}"},</Text>

      <Text style={emailStyles.lastParagraph}>
        We received a request to reset your password for your {"{{APP_NAME}}"} account. Click the button below to choose a new password:
      </Text>

      <div style={emailStyles.buttonRow}>
        <Button href="{{RESET_URL}}">Reset Password</Button>
      </div>

      <Text style={emailStyles.paragraph}>Or copy and paste this link into your browser:</Text>

      <Text style={emailStyles.linkBox}>{"{{RESET_URL}}"}</Text>

      <Text style={emailStyles.finePrint}>This link will expire in {"{{EXPIRES_HOURS}}"} hours.</Text>

      <Text style={emailStyles.closingNote}>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</Text>
    </Layout>
  )
}
