import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

import litestar from "litestar-vite-plugin";
const ASSET_URL =
  process.env.LITESTAR_ASSET_URL || process.env.ASSET_URL || "/static/";
const VITE_PORT = process.env.VITE_PORT || "5173";
const VITE_HOST = process.env.VITE_HOST || "localhost";
export default defineConfig({
  base: `${ASSET_URL}`,
  root: "src/app/domain/web",
  server: {
    host: `${VITE_HOST}`,
    port: +`${VITE_PORT}`,
    cors: true,
  },
  plugins: [
    vue(),
    litestar({
      input: ["src/app/domain/web/resources/main.ts"],
      assetUrl: `${ASSET_URL}`,
      assetDirectory: "resources/assets",
      bundleDirectory: "public",
      resourceDirectory: "resources",
      hotFile: "src/app/domain/web/public/hot",
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src/app/domain/web/resources"),
    },
  },
});
