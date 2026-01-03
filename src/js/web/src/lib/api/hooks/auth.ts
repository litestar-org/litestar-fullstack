import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { client } from "@/lib/generated/api/client.gen"
import {
  confirmMfaSetup,
  disableMfa,
  getMfaStatus,
  initiateMfaSetup,
  regenerateMfaBackupCodes,
  verifyMfaChallenge,
  type MfaBackupCodes,
  type MfaSetup,
  type MfaStatus,
  type OAuthAuthorization,
  type OffsetPaginationAppDomainAccountsSchemasOauthOAuthAccountInfo,
} from "@/lib/generated/api"

const bearerAuth = [{ scheme: "bearer", type: "http" }] as const

const fetchOAuthAccounts = async () => {
  const response = await client.get<OffsetPaginationAppDomainAccountsSchemasOauthOAuthAccountInfo>({
    url: "/api/profile/oauth/accounts",
    security: bearerAuth,
  })
  return response.data
}

const startOAuthLink = async (provider: string, redirectUrl: string) => {
  const response = await client.post<OAuthAuthorization>({
    url: `/api/profile/oauth/${provider}/link`,
    security: bearerAuth,
    query: { redirect_url: redirectUrl },
  })
  return response.data
}

const unlinkOAuthAccount = async (provider: string) => {
  const response = await client.delete({
    url: `/api/profile/oauth/${provider}`,
    security: bearerAuth,
  })
  return response.data
}

export function useMfaStatus() {
  return useQuery({
    queryKey: ["mfa", "status"],
    queryFn: async () => {
      const response = await getMfaStatus()
      return response.data as MfaStatus
    },
  })
}

export function useInitiateMfaSetup() {
  return useMutation({
    mutationFn: async () => {
      const response = await initiateMfaSetup()
      return response.data as MfaSetup
    },
  })
}

export function useConfirmMfaSetup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (code: string) => {
      const response = await confirmMfaSetup({ body: { code } })
      return response.data as MfaBackupCodes
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mfa", "status"] })
    },
  })
}

export function useDisableMfa() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (password: string) => {
      const response = await disableMfa({ body: { password } })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mfa", "status"] })
      toast.success("MFA disabled")
    },
  })
}

export function useRegenerateBackupCodes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (password: string) => {
      const response = await regenerateMfaBackupCodes({ body: { password } })
      return response.data as MfaBackupCodes
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mfa", "status"] })
      toast.success("Backup codes regenerated")
    },
  })
}

export function useVerifyMfaChallenge() {
  return useMutation({
    mutationFn: async (payload: { code?: string; recovery_code?: string }) => {
      const response = await verifyMfaChallenge({ body: payload })
      return response.data
    },
  })
}

export function useOAuthAccounts() {
  return useQuery({
    queryKey: ["profile", "oauth-accounts"],
    queryFn: fetchOAuthAccounts,
  })
}

export function useStartOAuthLink() {
  return useMutation({
    mutationFn: async (payload: { provider: string; redirectUrl: string }) => {
      return startOAuthLink(payload.provider, payload.redirectUrl)
    },
  })
}

export function useUnlinkOAuthAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (provider: string) => unlinkOAuthAccount(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", "oauth-accounts"] })
    },
  })
}
