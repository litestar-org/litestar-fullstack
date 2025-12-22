import { oAuthConfig, type OAuthConfig } from "@/lib/generated/api"
import { useQuery } from "@tanstack/react-query"

const defaultConfig: OAuthConfig = {
  googleEnabled: false,
  githubEnabled: false,
}

async function fetchOAuthConfig(): Promise<OAuthConfig> {
  const response = await oAuthConfig()

  if (response.error || !response.data) {
    return defaultConfig
  }

  return response.data
}

export function useOAuthConfig() {
  return useQuery({
    queryKey: ["oauth-config"],
    queryFn: fetchOAuthConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  })
}
