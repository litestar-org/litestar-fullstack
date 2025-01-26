import { defineConfig, defaultPlugins } from '@hey-api/openapi-ts';

export default defineConfig({
  input: './resources/openapi.json',
  output: './resources/lib/api',
  client: '@hey-api/client-axios',
   plugins: [
    "@hey-api/typescript",
    "zod",
    {
      name: "@hey-api/sdk",
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      operationId: true,
      methodNameBuilder: (operation) => {
        // @ts-ignore
        let name: string = operation.name || 'defaultName';
        // @ts-ignore
        let service: string = operation.service || '';

        if (service && name.toLowerCase().startsWith(service.toLowerCase())) {
          name = name.slice(service.length);
        }

        return name.charAt(0).toLowerCase() + name.slice(1);
      },
    },
  ],
});
