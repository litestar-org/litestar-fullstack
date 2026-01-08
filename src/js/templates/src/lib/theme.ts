/**
 * Centralized email theme constants
 *
 * This file provides a single source of truth for all email template styling.
 * Email templates use inline styles (required for email client compatibility),
 * so these constants ensure consistency across all templates.
 */

export const emailTheme = {
  colors: {
    // Brand colors
    brandNavy: "#0f1322",
    brandGold: "#FFB000",
    brandGoldHover: "#E59E00",

    // Background colors
    bodyBg: "#0f1322",
    containerBg: "#161b2c",
    footerBg: "#1c2237",
    codeBg: "#1c2237",

    // Border colors
    border: "#232d45",
    borderLight: "#2a3550",

    // Text colors
    textPrimary: "#f8f9fa",
    textHeading: "#f3f4f6",
    textBody: "#d1d5db",
    textMuted: "#9ca3af",
    textFooter: "#6b7280",

    // Button variant colors
    successBg: "#22c55e",
    successHover: "#16a34a",
    secondaryBg: "#374151",
    secondaryHover: "#4b5563",
  },

  fonts: {
    primary: "'Manrope', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif",
  },

  spacing: {
    bodyPadding: "40px 20px",
    containerPadding: "36px 40px",
    headerPadding: "24px 32px",
    footerPadding: "24px 32px",
  },

  radius: {
    container: "12px",
    button: "8px",
    code: "8px",
  },

  shadows: {
    container: "0 8px 32px rgba(0, 0, 0, 0.2)",
  },

  lineHeight: "1.6",
} as const

// Type for the theme
export type EmailTheme = typeof emailTheme
