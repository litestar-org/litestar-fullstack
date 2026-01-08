import { Text } from "@react-email/components"
import { emailTheme } from "../lib/theme"

interface FooterProps {
  appName: string
}

export const Footer = ({ appName }: FooterProps) => {
  const year = new Date().getFullYear()

  return (
    <div
      style={{
        backgroundColor: emailTheme.colors.footerBg,
        padding: emailTheme.spacing.footerPadding,
        textAlign: "center" as const,
        borderTop: `1px solid ${emailTheme.colors.border}`,
      }}
    >
      <Text
        style={{
          margin: "0 0 8px 0",
          color: emailTheme.colors.textMuted,
          fontSize: "12px",
        }}
      >
        {appName}
      </Text>
      <Text
        style={{
          margin: 0,
          color: emailTheme.colors.textFooter,
          fontSize: "11px",
        }}
      >
        &copy; {year} All rights reserved.
      </Text>
      <Text
        style={{
          margin: "8px 0 0 0",
          color: emailTheme.colors.textFooter,
          fontSize: "11px",
        }}
      >
        You received this email because you have an account with {appName}.
      </Text>
    </div>
  )
}
