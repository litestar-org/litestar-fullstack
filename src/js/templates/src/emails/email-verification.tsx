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
import { emailStyles } from "../lib/theme"

export default function EmailVerification() {
  return (
    <Layout preview="Verify your email address" appName="{{APP_NAME}}">
      <Heading style={emailStyles.heading}>Verify your email address</Heading>

      <Text style={emailStyles.paragraph}>Hi {"{{USER_NAME}}"},</Text>

      <Text style={emailStyles.lastParagraph}>Thank you for signing up for {"{{APP_NAME}}"}. Please verify your email address by clicking the button below:</Text>

      <div style={emailStyles.buttonRow}>
        <Button href="{{VERIFICATION_URL}}">Verify Email Address</Button>
      </div>

      <Text style={emailStyles.paragraph}>Or copy and paste this link into your browser:</Text>

      <Text style={emailStyles.linkBox}>{"{{VERIFICATION_URL}}"}</Text>

      <Text style={emailStyles.finePrint}>This link will expire in {"{{EXPIRES_HOURS}}"} hours.</Text>

      <Text style={emailStyles.closingNote}>If you didn't create an account with {"{{APP_NAME}}"}, you can safely ignore this email.</Text>
    </Layout>
  )
}
