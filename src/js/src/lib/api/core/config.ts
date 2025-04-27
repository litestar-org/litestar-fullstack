import type { ClientOptions } from '../types.gen';
import { type Config } from '@hey-api/client-axios';

export const createClientConfig = <T extends ClientOptions>(
  override?: Config<T>
): Config<Required<T>> => ({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  ...override,
});
