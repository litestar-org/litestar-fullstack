/** @type {import('tailwindcss').Config} */
// Tailwind v4 uses CSS for configuration, but we keep this file for compatibility
// with tooling that expects it, or for complex plugins that might not work with v4's CSS-first approach yet.
// However, most of the theme is now defined in src/styles.css via @theme.

export default {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
