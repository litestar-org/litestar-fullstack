import { useMutation, useQuery } from "@tanstack/react-query"
import { publicAuthConfigOptions, securityStepUpMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

const AUTH_CONFIG_STALE_TIME_MS = 5 * 60 * 1000

export function useAuthConfig() {
  return useQuery({
    ...publicAuthConfigOptions(),
    staleTime: AUTH_CONFIG_STALE_TIME_MS,
    retry: false,
  })
}

export function useStepUpGrant() {
  const stepUp = useMutation(securityStepUpMutation())

  const requestGrant = async (purpose: string, password: string): Promise<string> => {
    const { grant } = await stepUp.mutateAsync({
      path: { purpose },
      body: { method: "password", credential: password },
    })
    return grant
  }

  return {
    requestGrant,
    isPending: stepUp.isPending,
  }
}
