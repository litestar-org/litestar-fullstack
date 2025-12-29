import { Button as EmailButton } from "@react-email/components"
import type { ReactNode } from "react"

interface ButtonProps {
  href: string
  children: ReactNode
  variant?: "primary" | "success" | "secondary"
}

export const Button = ({ href, children, variant = "primary" }: ButtonProps) => {
  const colors = {
    primary: {
      background: "#202235",
      hover: "#3a3f5c",
    },
    success: {
      background: "#22c55e",
      hover: "#16a34a",
    },
    secondary: {
      background: "#6b7280",
      hover: "#4b5563",
    },
  }

  const { background } = colors[variant]

  return (
    <EmailButton
      href={href}
      style={{
        display: "inline-block",
        padding: "12px 32px",
        backgroundColor: background,
        color: "#ffffff",
        textDecoration: "none",
        borderRadius: "6px",
        fontWeight: 500,
        fontSize: "14px",
        lineHeight: "20px",
        textAlign: "center" as const,
      }}
    >
      {children}
    </EmailButton>
  )
}
