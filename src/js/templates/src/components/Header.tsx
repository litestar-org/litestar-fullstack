import { Heading, Text } from "@react-email/components"

interface HeaderProps {
  appName: string
}

export const Header = ({ appName }: HeaderProps) => {
  return (
    <div
      style={{
        backgroundColor: "#202235",
        padding: "24px 32px",
        textAlign: "center" as const,
      }}
    >
      <Heading
        style={{
          margin: 0,
          color: "#ffffff",
          fontSize: "24px",
          fontWeight: 600,
          letterSpacing: "-0.5px",
        }}
      >
        {appName}
      </Heading>
      <Text
        style={{
          margin: "4px 0 0 0",
          color: "rgba(255, 255, 255, 0.8)",
          fontSize: "12px",
          fontWeight: 400,
        }}
      >
        Secure Application Platform
      </Text>
    </div>
  )
}
