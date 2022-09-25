import { authInstance } from "@/plugins/auth/plugin"
import { AuthPlugin } from "@/plugins/auth/types"

/**
 * Returns the auth instance. Equivalent to using `$auth` inside
 * templates.
 */
export function useAuth(): AuthPlugin {
  // eslint-disable-next-line
  return authInstance!
}
