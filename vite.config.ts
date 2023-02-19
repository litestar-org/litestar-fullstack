import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

function getBackendUrl(path: string) {
  return `${process.env.FRONTEND_URL || "http://localhost:8000"}${path}`;
}
const STATIC_URL = process.env.STATIC_URL || "/static/";
export default defineConfig({
  base: `${STATIC_URL}`,
  root: path.join(__dirname, "src/app/domain/web/resources"),
  optimizeDeps: {
    force: true,
  },
  server: {
    fs: {
      allow: [".", path.join(__dirname, "node_modules")],
    },
    port: 3000,
    cors: true,
    strictPort: true,
    watch: {
      ignored: ["node_modules", ".venv", "**/__pycache__/**"],
    },
    proxy: {
      "/api": {
        target: getBackendUrl("/api"),
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },

  plugins: [vue()],
  build: {
    target: "esnext",
    outDir: "../public",
    emptyOutDir: true,
    assetsDir: "assets/",
    manifest: true,
    rollupOptions: {
      input: path.join(__dirname, "src/app/domain/web/resources/main.ts"),
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            return id
              .toString()
              .split("node_modules/")[1]
              .split("/")[0]
              .toString();
          }
        },
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src/app/domain/web/resources"),
    },
  },
});
