import { Button as EmailButton } from "@react-email/components"
import type { ReactNode } from "react"
import { emailTheme } from "../lib/theme"

const VARIANT_COLORS = {
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

interface ButtonProps {
  href: string
  children: ReactNode
  variant?: keyof typeof VARIANT_COLORS
}

export const Button = ({ href, children, variant = "primary" }: Readonly<ButtonProps>) => {
  const { background, color } = VARIANT_COLORS[variant]

  return (
    <EmailButton
      href={href}
      style={{
        display: "inline-block",
        padding: "12px 32px",
        backgroundColor: background,
        color,
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
