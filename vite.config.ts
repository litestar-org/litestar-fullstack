import { defineConfig } from "vite"
import path from "path"
import litestar from "litestar-vite-plugin"
import react from "@vitejs/plugin-react"

const ASSET_URL = process.env.ASSET_URL || "/static/"
const VITE_PORT = process.env.VITE_PORT || "5173"
export default defineConfig({
  base: `${ASSET_URL}`,
  clearScreen: false,
  server: {
    host: "0.0.0.0",
    port: +`${VITE_PORT}`,
    cors: true,
  },
  plugins: [
    react(),
    litestar({
      input: ["resources/main.tsx"],
      assetUrl: `${ASSET_URL}`,
      bundleDirectory: "src/app/domain/web/public",
      resourceDirectory: "resources",
      hotFile: "src/app/domain/web/public/hot",
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "resources"),
    },
  },
})
