import { useQuery } from "@tanstack/react-query"

interface OAuthConfig {
  googleEnabled: boolean
  githubEnabled: boolean
}

async function fetchOAuthConfig(): Promise<OAuthConfig> {
  const response = await fetch("/api/config/oauth", {
    method: "GET",
    credentials: "include",
  })

  if (!response.ok) {
    // If the endpoint doesn't exist or fails, assume OAuth is disabled
    return { googleEnabled: false, githubEnabled: false }
  }

  return response.json()
}

export function useOAuthConfig() {
  return useQuery({
    queryKey: ["oauth-config"],
    queryFn: fetchOAuthConfig,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  })
}
