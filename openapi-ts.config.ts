import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: './resources/openapi.json',
  output: './resources/lib/api',
  client: "legacy/axios",
   // exportSchemas: true,
   plugins: [
    {
      name: "@hey-api/sdk",
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      operationId: true,
      methodNameBuilder: (operation) => {
        // @ts-ignore
        let name: string = operation.name
        // @ts-ignore
        let service: string = operation.service

        if (service && name.toLowerCase().startsWith(service.toLowerCase())) {
          name = name.slice(service.length)
        }

        return name.charAt(0).toLowerCase() + name.slice(1)
      },
    },
  ],
});
