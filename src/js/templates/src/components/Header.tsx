import { Heading, Text } from "@react-email/components"
import { emailTheme } from "../lib/theme"

interface HeaderProps {
  appName: string
}

export const Header = ({ appName }: HeaderProps) => {
  return (
    <div
      style={{
        backgroundColor: emailTheme.colors.brandGold,
        padding: emailTheme.spacing.headerPadding,
        textAlign: "center" as const,
      }}
    >
      <Heading
        style={{
          margin: 0,
          color: emailTheme.colors.brandNavy,
          fontSize: "24px",
          fontWeight: 700,
          letterSpacing: "-0.5px",
        }}
      >
        {appName}
      </Heading>
      <Text
        style={{
          margin: "4px 0 0 0",
          color: `${emailTheme.colors.brandNavy}cc`, // 80% opacity
          fontSize: "12px",
          fontWeight: 500,
        }}
      >
        Secure Application Platform
      </Text>
    </div>
  )
}
