import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

import litestar from "litestar-vite-plugin";

const ASSET_URL = process.env.STATIC_URL || "/static/";
export default defineConfig({
  base: `${ASSET_URL}`,
  root: "src/app/domain/web",
  server: {
    host: "localhost",
    port: 3005,
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
