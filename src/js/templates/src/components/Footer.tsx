import { Text } from "@react-email/components"

interface FooterProps {
  appName: string
}

export const Footer = ({ appName }: FooterProps) => {
  const year = new Date().getFullYear()

  return (
    <div
      style={{
        backgroundColor: "#f8f9fa",
        padding: "24px 32px",
        textAlign: "center" as const,
        borderTop: "1px solid #DCDFE4",
      }}
    >
      <Text
        style={{
          margin: "0 0 8px 0",
          color: "#5f6368",
          fontSize: "12px",
        }}
      >
        {appName}
      </Text>
      <Text
        style={{
          margin: 0,
          color: "#9aa0a6",
          fontSize: "11px",
        }}
      >
        &copy; {year} All rights reserved.
      </Text>
      <Text
        style={{
          margin: "8px 0 0 0",
          color: "#9aa0a6",
          fontSize: "11px",
        }}
      >
        You received this email because you have an account with {appName}.
      </Text>
    </div>
  )
}
