import { startAuthentication } from "@simplewebauthn/browser"
import { toast } from "sonner"
import { create } from "zustand"
import { persist } from "zustand/middleware"
import { extractApiErrorMessage, isApplicationAccessRequired } from "@/lib/api-client"
import type { LocalMfaChallenge, Team, User } from "@/lib/generated/api"
import { accountProfile, localSessionLogin, localSessionLogout, passkeyAuthenticationOptions, passkeyAuthenticationVerify } from "@/lib/generated/api"

export interface LoginResult {
  authenticated: boolean
  mfaRequired: boolean
  challengeToken?: string
  accountId?: string
  methods?: string[]
  totpMethodIds?: string[]
}

export interface PendingMfaChallenge {
  accountId: string
  challenge: string
  methods: string[]
  totpMethodIds: string[]
}

export interface AuthState {
  user: User | null
  currentTeam: Team | null
  teams: Team[]
  isLoading: boolean
  isAuthenticated: boolean
  mfaChallenge: PendingMfaChallenge | null
  login: (email: string, password: string) => Promise<LoginResult>
  loginWithPasskey: (accountId?: string) => Promise<boolean>
  completeMfaLogin: () => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<boolean>
  clearSession: () => void
  setCurrentTeam: (team: Team) => void
  setTeams: (teams: Team[]) => void
}

function isMfaChallengePayload(error: unknown): error is LocalMfaChallenge {
  return (
    typeof error === "object" &&
    error !== null &&
    "challenge" in error &&
    "account_id" in error &&
    typeof (error as { challenge?: unknown }).challenge === "string" &&
    typeof (error as { account_id?: unknown }).account_id === "string"
  )
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      currentTeam: null,
      teams: [],
      isLoading: false,
      isAuthenticated: false,
      mfaChallenge: null,
      clearSession: () =>
        set({
          user: null,
          currentTeam: null,
          teams: [],
          isAuthenticated: false,
          mfaChallenge: null,
        }),
      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const {
            data: session,
            error: loginError,
            response,
          } = await localSessionLogin({
            body: { identifier: email, password },
          })

          if (response?.status === 403 && isMfaChallengePayload(loginError)) {
            const methods = Array.isArray(loginError.methods) ? loginError.methods : ["totp"]
            const totpMethodIds = Array.isArray(loginError.totp_method_ids) ? loginError.totp_method_ids : []
            set({
              user: null,
              isAuthenticated: false,
              mfaChallenge: {
                accountId: loginError.account_id,
                challenge: loginError.challenge,
                methods,
                totpMethodIds,
              },
            })
            return {
              authenticated: false,
              mfaRequired: true,
              challengeToken: loginError.challenge,
              accountId: loginError.account_id,
              methods,
              totpMethodIds,
            }
          }

          if (session) {
            const { data: user, error: profileError } = await accountProfile()
            if (user) {
              set({ user, isAuthenticated: true, mfaChallenge: null })
              return { authenticated: true, mfaRequired: false }
            }
            if (isApplicationAccessRequired(profileError)) {
              // The API client's access-denied handler signs the user out and explains why.
              get().clearSession()
              return { authenticated: false, mfaRequired: false }
            }
          }

          get().clearSession()
          toast.error(extractApiErrorMessage(loginError, "Invalid email or password"))
          return { authenticated: false, mfaRequired: false }
        } catch (error) {
          get().clearSession()
          toast.error("Sign in failed", {
            description: extractApiErrorMessage(error, "Unknown error"),
          })
          return { authenticated: false, mfaRequired: false }
        } finally {
          set({ isLoading: false })
        }
      },
      loginWithPasskey: async (accountId?: string) => {
        const resolvedAccountId = accountId?.trim() || undefined

        set({ isLoading: true })
        try {
          const { data: ceremony, error: ceremonyError } = await passkeyAuthenticationOptions({
            body: resolvedAccountId ? { account_id: resolvedAccountId } : {},
          })
          if (!ceremony) {
            toast.error(extractApiErrorMessage(ceremonyError, "Unable to start passkey sign-in"))
            return false
          }

          const optionsJSON = JSON.parse(ceremony.options)
          const assertion = await startAuthentication({ optionsJSON })
          const { error: verificationError } = await passkeyAuthenticationVerify({
            body: {
              ...(resolvedAccountId ? { account_id: resolvedAccountId } : {}),
              binding: ceremony.binding ?? undefined,
              response: JSON.stringify(assertion),
            },
          })

          if (verificationError) {
            toast.error(extractApiErrorMessage(verificationError, "Passkey authentication failed"))
            return false
          }

          return await get().checkAuth()
        } catch (error) {
          if (error instanceof Error && (error.name === "AbortError" || error.name === "NotAllowedError")) {
            toast.info("Passkey sign-in was cancelled")
            return false
          }
          toast.error("Passkey sign-in failed", {
            description: extractApiErrorMessage(error, "Unknown error"),
          })
          return false
        } finally {
          set({ isLoading: false })
        }
      },
      completeMfaLogin: async () => {
        set({ isLoading: true })
        try {
          const { data: user, error: profileError } = await accountProfile()
          if (user) {
            set({ user, isAuthenticated: true, mfaChallenge: null })
            return
          }
          get().clearSession()
          throw new Error(extractApiErrorMessage(profileError, "Unable to complete MFA sign-in"))
        } finally {
          set({ isLoading: false })
        }
      },
      logout: async () => {
        set({ isLoading: true })
        try {
          await localSessionLogout()
        } finally {
          get().clearSession()
          set({ isLoading: false })
        }
      },
      checkAuth: async () => {
        set({ isLoading: true })
        try {
          const { data: user, error: profileError, response } = await accountProfile()
          if (user) {
            set({ user, isAuthenticated: true })
            return true
          }

          const status = response?.status
          if (status !== undefined && status >= 500) {
            throw new Error(extractApiErrorMessage(profileError, `Authentication service unavailable (${status})`))
          }

          get().clearSession()
          return false
        } finally {
          set({ isLoading: false })
        }
      },
      setCurrentTeam: (team: Team) => set({ currentTeam: team }),
      setTeams: (teams: Team[]) =>
        set((state) => {
          const isCurrentTeamListed = teams.some((team) => team.id === state.currentTeam?.id)
          return { teams, currentTeam: isCurrentTeamListed ? state.currentTeam : (teams[0] ?? null) }
        }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
