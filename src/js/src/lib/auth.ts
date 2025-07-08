import { accountLogin, accountLogout, accountProfile } from "@/lib/api/sdk.gen"
import type { Team, User } from "@/lib/api/types.gen"
import { toast } from "sonner"
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface AuthState {
  user: User | null
  currentTeam: Team | null
  teams: Team[]
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  setCurrentTeam: (team: Team) => void
  setTeams: (teams: Team[]) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      currentTeam: null,
      teams: [],
      isLoading: false,
      isAuthenticated: false,
      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          // Login request
          const response = await accountLogin({ body: { username: email, password } })

          if (response.status === 201) {
            // Add a small delay to ensure the cookie is set
            await new Promise((resolve) => setTimeout(resolve, 100))

            // Verify the authentication by getting the profile
            const { data: user } = await accountProfile()
            // TODO: Maybe add a check for user here?
            set({ user, isAuthenticated: true })
            return
          }

          set({ user: null, currentTeam: null, isAuthenticated: false })
          toast.error(response.error?.detail || "Login failed")
        } catch (error) {
          set({ user: null, currentTeam: null, isAuthenticated: false })
          toast.error("An error occurred", {
            description: error instanceof Error ? error.message : "Unknown error",
          })
        } finally {
          set({ isLoading: false })
        }
      },
      logout: async () => {
        set({ isLoading: true })
        try {
          await accountLogout()
          set({ user: null, currentTeam: null, isAuthenticated: false })
        } finally {
          set({ isLoading: false })
        }
      },
      checkAuth: async () => {
        set({ isLoading: true })
        try {
          const { data: user } = await accountProfile()
          set({ user, isAuthenticated: true })
        } catch {
          set({ user: null, currentTeam: null, isAuthenticated: false })
        } finally {
          set({ isLoading: false })
        }
      },
      setCurrentTeam: (team: Team) => set({ currentTeam: team }),
      setTeams: (teams: Team[]) => set({ teams }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    },
  ),
)
