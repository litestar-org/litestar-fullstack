import vueI18n from "@intlify/vite-plugin-vue-i18n"
import vue from "@vitejs/plugin-vue"
import path from "path"
import { defineConfig } from "vite"
import eslintPlugin from "vite-plugin-eslint"

const Dotenv = require("dotenv")

Dotenv.config({ path: path.join(__dirname, ".env") })

// function getStaticUrl() {
//   return process.env.GLUENT_CONSOLE_STATIC_URL
// }
function getBackendUrl(path) {
  return `${process.env.GLUENT_CONSOLE_BACKEND_URL || "http://127.0.0.1:8000"}${path}`
}
// https://vitejs.dev/config/
export default defineConfig({
  envPrefix: ["GLUENT_CONSOLE_"],
  root: path.join(__dirname, "src/frontend"),
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
  plugins: [
    vue(),
    eslintPlugin(),
    vueI18n({
      include: path.resolve(__dirname, "src/frontend/locales/**"),
    }),
  ],
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
      "@": path.resolve(__dirname, "src/frontend/src/"),
      moment: "dayjs",
      "vue-i18n": "vue-i18n/dist/vue-i18n.runtime.esm-bundler.js",
    },
  },
})
