import { startAuthentication } from "@simplewebauthn/browser"
import { toast } from "sonner"
import { create } from "zustand"
import { persist } from "zustand/middleware"
import { extractApiErrorMessage } from "@/lib/api-client"
import type { LocalMfaChallenge, Team, User } from "@/lib/generated/api"
import { accountProfile, localSessionLogin, localSessionLogout, passkeyAuthenticationOptions, passkeyAuthenticationVerify } from "@/lib/generated/api"

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

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
  passkeyAccountId: string | null
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
      passkeyAccountId: null,
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
              set({
                user: profileRes.data,
                isAuthenticated: true,
                passkeyAccountId: profileRes.data.id,
                mfaChallenge: null,
              })
              return { authenticated: true, mfaRequired: false }
            }
          }

          get().clearSession()
          toast.error(extractApiErrorMessage(response.error, "Invalid email or password"))
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
        const resolvedAccountId = accountId?.trim() || get().passkeyAccountId || ""
        if (!UUID_PATTERN.test(resolvedAccountId)) {
          toast.error("Passkey sign-in requires a recognized account on this device. Sign in with your password first.")
          return false
        }

        set({ isLoading: true })
        try {
          const optionsRes = await passkeyAuthenticationOptions({
            body: { account_id: resolvedAccountId },
          })
          if (!optionsRes.data) {
            toast.error(extractApiErrorMessage(optionsRes.error, "Unable to start passkey sign-in"))
            return false
          }

          const optionsJSON = JSON.parse(optionsRes.data.options)
          const assertion = await startAuthentication({ optionsJSON })
          const verifyRes = await passkeyAuthenticationVerify({
            body: {
              account_id: resolvedAccountId,
              binding: optionsRes.data.binding ?? undefined,
              response: JSON.stringify(assertion),
            },
          })

          if (verifyRes.error) {
            toast.error(extractApiErrorMessage(verifyRes.error, "Passkey authentication failed"))
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
          const profileRes = await accountProfile()
          if (profileRes.data) {
            set({
              user: profileRes.data,
              isAuthenticated: true,
              passkeyAccountId: profileRes.data.id,
              mfaChallenge: null,
            })
            return
          }
          get().clearSession()
          throw new Error(extractApiErrorMessage(profileRes.error, "Unable to complete MFA sign-in"))
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
            set({ user: response.data, isAuthenticated: true, passkeyAccountId: response.data.id })
            return true
          }

          if (status !== undefined && status >= 500) {
            throw new Error(extractApiErrorMessage(response.error, `Authentication service unavailable (${status})`))
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
        passkeyAccountId: state.passkeyAccountId,
      }),
    },
  ),
)
