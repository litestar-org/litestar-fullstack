import vue from "@vitejs/plugin-vue"
import path from "path"
import { defineConfig } from "vite"
import eslintPlugin from "vite-plugin-eslint"

const Dotenv = require("dotenv")

Dotenv.config({ path: path.join(__dirname, ".env") })

function getBackendUrl(path) {
  return `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}${path}`
}
// https://vitejs.dev/config/
export default defineConfig({
  root: path.join(__dirname, "src/ui"),
  logLevel: "info",
  // base: getStaticUrl(),
  // publicDir: path.join(__dirname, "src/frontend/public"),
  server: {
    fs: {
      allow: [".", path.join(__dirname, "node_modules")],
    },
    port: 3000,
    cors: true,
    force: true,
    strictPort: true,
    watch: {
      ignored: [
        "**/.venv/**",
        "./deploy",
        "/docs",
        "src/backend/**",
        "node_modules",
        "scripts",
        "**/thirdparty/**",
        "**/target/**",
        "**/__pycache__/**",
      ],
    },
    proxy: {
      "/api": {
        target: getBackendUrl("/api"),
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/docs": {
        target: getBackendUrl("/docs"),
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/docs/, ""),
      },
    },
  },
  optimizeDeps: {
    include: [
      "vue",
      "@headlessui/vue",
      "axios",
      "pinia",
      "@vueuse/head",
      "vue-router",
      "@heroicons/vue/outline",
      "@heroicons/vue/solid",
      "chart.js",
    ],
  },
  plugins: [vue(), eslintPlugin()],
  build: {
    target: "esnext",
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "assets/",
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            return id.toString().split("node_modules/")[1].split("/")[0].toString()
          }
        },
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src/ui/src/"),
    },
  },
})
