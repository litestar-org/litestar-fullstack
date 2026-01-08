import { Button as EmailButton } from "@react-email/components"
import type { ReactNode } from "react"
import { emailTheme } from "../lib/theme"

interface ButtonProps {
  href: string
  children: ReactNode
  variant?: "primary" | "success" | "secondary"
}

export const Button = ({ href, children, variant = "primary" }: ButtonProps) => {
  const colors = {
    primary: {
      background: emailTheme.colors.brandGold,
      color: emailTheme.colors.brandNavy,
    },
    success: {
      background: emailTheme.colors.successBg,
      color: "#ffffff",
    },
    secondary: {
      background: emailTheme.colors.secondaryBg,
      color: "#ffffff",
    },
  }

  const { background, color } = colors[variant]

  return (
    <EmailButton
      href={href}
      style={{
        display: "inline-block",
        padding: "12px 32px",
        backgroundColor: background,
        color: color,
        textDecoration: "none",
        borderRadius: emailTheme.radius.button,
        fontWeight: 600,
        fontSize: "14px",
        lineHeight: "20px",
        textAlign: "center" as const,
      }}
    >
      {children}
    </EmailButton>
  )
}
