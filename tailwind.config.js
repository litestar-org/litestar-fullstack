/* eslint-disable @typescript-eslint/no-var-requires */
const defaultTheme = require("tailwindcss/defaultTheme")

module.exports = {
  darkMode: "class", // or 'media' or 'class'
  content: ["src/ui/src/**/*.{vue,js,ts,jsx,tsx,html}"],
  plugins: [require("@tailwindcss/forms"), require("@tailwindcss/typography"), require("@tailwindcss/aspect-ratio")],
}
