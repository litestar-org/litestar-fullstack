import type { Config } from "@hey-api/client-axios";
import type { ClientOptions } from "../types.gen";

export const createClientConfig = <T extends ClientOptions>(override?: Config<T>): Config<Required<T>> => ({
  baseURL: import.meta.env.API_URL,
  ...override,
});
