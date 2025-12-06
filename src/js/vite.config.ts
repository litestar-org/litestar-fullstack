import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react"
import litestar from "litestar-vite-plugin"
import { type PluginOption, defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    // TanStack Router plugin must come before React plugin
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    tailwindcss(),
    react(),
    ...(litestar({
      input: ["src/main.tsx"],
      assetUrl: process.env.ASSET_URL || "/",
      bundleDirectory: "../py/app/server/public",
      resourceDirectory: "src",
      // Disable built-in type generation - using custom @hey-api/openapi-ts config
      types: false,
    }) as PluginOption[]),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
