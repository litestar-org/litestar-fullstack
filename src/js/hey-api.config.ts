import type { Config } from "@hey-api/client-axios";

const config: Config = {
  input: "src/openapi.json",
  output: "src/lib/api",
  plugins: [
    {
      name: "@hey-api/client-axios",
      runtimeConfigPath: "./src/lib/api/core/config.ts",
    },
  ],
  exportCore: true,
  exportServices: true,
  exportModels: true,
  exportSchemas: true,
  useOptions: true,
  useUnionTypes: true,
  name: "ApiClient",
  postfixServices: "Service",
  postfixModels: "",
  enumNames: true,
  operationId: true,
  format: true,
  types: {
    dates: "string",
    enums: "typescript",
    numbers: "string",
  },
  schemas: {
    export: true,
    type: "zod",
  },
};

export default config;
