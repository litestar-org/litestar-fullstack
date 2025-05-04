/// <reference types="vite/client" />
import type { Config } from "@hey-api/client-axios";
import type { ClientOptions } from "./src/lib/api/types.gen";

// Hey API codegen config (default export)
const config = {
  input: "src/openapi.json",
  output: "src/lib/api",
  plugins: [
    {
      name: "@hey-api/client-axios",
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

// Runtime config for your app (named export)
export const createClientConfig = <T extends ClientOptions>(override?: Config<T>): Config<Required<T>> => ({
  baseURL: import.meta.env.API_URL,
  ...override,
});
