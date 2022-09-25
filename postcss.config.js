module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
    "tailwindcss/nesting": {},
    "postcss-import": {},
    ...(process.env.NODE_ENV === "production" ? { cssnano: {} } : {}),
  },
}
