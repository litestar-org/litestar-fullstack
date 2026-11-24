import { useMutation } from "@tanstack/react-query"
import { securityStepUpMutation } from "@/lib/generated/api/@tanstack/react-query.gen"

export function useStepUpGrant() {
  const stepUp = useMutation(securityStepUpMutation())

  const requestGrant = async (purpose: string, password: string): Promise<string> => {
    const grant = await stepUp.mutateAsync({
      path: { purpose },
      body: { method: "password", credential: password },
    })
    return grant.grant
  }

  return {
    requestGrant,
    isPending: stepUp.isPending,
  }
}
