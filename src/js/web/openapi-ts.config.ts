import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "src/lib/generated/openapi.json",
  output: {
    path: "src/lib/generated/api",
    format: "prettier",
  },
  plugins: [
    "@hey-api/typescript",
    "@hey-api/schemas",
    {
      name: "@hey-api/sdk",
      asClass: false,
      operationId: true,
    },
    {
      name: "@tanstack/react-query",
      queryOptions: true,
      mutationOptions: true,
    },
  ],
})
