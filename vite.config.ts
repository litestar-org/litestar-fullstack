import { defineConfig } from "vite"
import path from "path"
import litestar from "litestar-vite-plugin"
import react from "@vitejs/plugin-react"

const ASSET_URL =
  process.env.LITESTAR_ASSET_URL || process.env.ASSET_URL || "/static/"
const VITE_PORT = process.env.VITE_PORT || "5173"
const VITE_HOST = process.env.VITE_HOST || "localhost"
export default defineConfig({
  base: `${ASSET_URL}`,
  clearScreen: false,
  server: {
    host: `${VITE_HOST}`,
    port: +`${VITE_PORT}`,
    cors: true,
  },
  plugins: [
    react(),
    litestar({
      input: ["resources/main.tsx"],
      assetUrl: `${ASSET_URL}`,
      bundleDirectory: "src/app/domain/web/static",
      resourceDirectory: "resources",
      hotFile: "public/hot",
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "resources"),
    },
  },
})
