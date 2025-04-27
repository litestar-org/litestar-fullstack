import type { Config, ClientOptions } from '@hey-api/client-axios';

export const createClientConfig = <T extends ClientOptions>(
  override?: Config<T>
): Config<Required<ClientOptions> & T> => {
  return {
    baseURL: '/api',
    ...override,
  };
};
