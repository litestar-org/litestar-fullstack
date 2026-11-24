import { startAuthentication } from "@simplewebauthn/browser"
import { toast } from "sonner"
import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { LocalMfaChallenge, Team, User } from "@/lib/generated/api"
import { accountProfile, localSessionLogin, localSessionLogout, passkeyAuthenticationOptions, passkeyAuthenticationVerify } from "@/lib/generated/api"

export interface LoginResult {
  authenticated: boolean
  mfaRequired: boolean
  challengeToken?: string
  accountId?: string
  methods?: string[]
}

export interface PendingMfaChallenge {
  accountId: string
  challenge: string
  methods: string[]
}

export interface AuthState {
  user: User | null
  currentTeam: Team | null
  teams: Team[]
  isLoading: boolean
  isAuthenticated: boolean
  mfaChallenge: PendingMfaChallenge | null
  login: (email: string, password: string) => Promise<LoginResult>
  loginWithPasskey: (accountIdentifier?: string) => Promise<boolean>
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

function extractErrorDetail(error: unknown, fallback: string): string {
  if (typeof error === "object" && error !== null && "detail" in error) {
    const detail = (error as { detail?: unknown }).detail
    if (typeof detail === "string" && detail.length > 0) {
      return detail
    }
  }
  return fallback
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
          const response = await localSessionLogin({
            body: { identifier: email, password },
          })

          if (response.response?.status === 403 && isMfaChallengePayload(response.error)) {
            const methods = Array.isArray(response.error.methods) ? response.error.methods : ["totp"]
            set({
              user: null,
              isAuthenticated: false,
              mfaChallenge: {
                accountId: response.error.account_id,
                challenge: response.error.challenge,
                methods,
              },
            })
            return {
              authenticated: false,
              mfaRequired: true,
              challengeToken: response.error.challenge,
              accountId: response.error.account_id,
              methods,
            }
          }

          if (response.data) {
            const profileRes = await accountProfile()
            if (profileRes.data) {
              set({ user: profileRes.data, isAuthenticated: true, mfaChallenge: null })
              return { authenticated: true, mfaRequired: false }
            }
          }

          get().clearSession()
          toast.error(extractErrorDetail(response.error, "Invalid email or password"))
          return { authenticated: false, mfaRequired: false }
        } catch (error) {
          get().clearSession()
          toast.error("Sign in failed", {
            description: error instanceof Error ? error.message : "Unknown error",
          })
          return { authenticated: false, mfaRequired: false }
        } finally {
          set({ isLoading: false })
        }
      },
      loginWithPasskey: async (accountIdentifier?: string) => {
        set({ isLoading: true })
        try {
          const optionsRes = await passkeyAuthenticationOptions({
            body: { account_id: accountIdentifier ?? "" },
          })
          if (!optionsRes.data) {
            toast.error(extractErrorDetail(optionsRes.error, "Unable to start passkey sign-in"))
            return false
          }

          const optionsJSON = JSON.parse(optionsRes.data.options)
          const assertion = await startAuthentication({ optionsJSON })
          const verifyRes = await passkeyAuthenticationVerify({
            body: {
              account_id: accountIdentifier ?? "",
              binding: optionsRes.data.binding ?? undefined,
              response: JSON.stringify(assertion),
            },
          })

          if (verifyRes.error) {
            toast.error(extractErrorDetail(verifyRes.error, "Passkey authentication failed"))
            return false
          }

          return await get().checkAuth()
        } catch (error) {
          if (error instanceof Error && (error.name === "AbortError" || error.name === "NotAllowedError")) {
            toast.info("Passkey sign-in was cancelled")
            return false
          }
          toast.error("Passkey sign-in failed", {
            description: error instanceof Error ? error.message : "Unknown error",
          })
          return false
        } finally {
          set({ isLoading: false })
        }
      },
      completeMfaLogin: async () => {
        set({ isLoading: true })
        try {
          const profileRes = await accountProfile()
          if (profileRes.data) {
            set({ user: profileRes.data, isAuthenticated: true, mfaChallenge: null })
            return
          }
          get().clearSession()
          throw new Error(extractErrorDetail(profileRes.error, "Unable to complete MFA sign-in"))
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
          const response = await accountProfile()
          const status = response.response?.status

          if (response.data) {
            set({ user: response.data, isAuthenticated: true })
            return true
          }

          if (status !== undefined && status >= 500) {
            throw new Error(extractErrorDetail(response.error, `Authentication service unavailable (${status})`))
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
          const nextCurrent = state.currentTeam && teams.some((team) => team.id === state.currentTeam?.id) ? state.currentTeam : (teams[0] ?? null)
          return { teams, currentTeam: nextCurrent }
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
