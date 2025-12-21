import { accountLogout } from "@/lib/generated/api/sdk.gen"
import { create } from "zustand"

interface User {
  id: string
  email: string
  avatar_url: string | null
  is_verified?: boolean
  email_verified_at?: string | null
}

interface AuthState {
  user: User | null
  isLoading: boolean
  error: string | null
  setUser: (user: User | null) => void
  setError: (error: string | null) => void
  logout: () => Promise<void>
  refetch: () => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  error: null,
  setUser: (user) => set({ user, isLoading: false }),
  setError: (error) => set({ error, isLoading: false }),
  logout: async () => {
    try {
      await accountLogout()
      set({ user: null, isLoading: false, error: null })
    } catch (error) {
      set({ error: "Failed to logout", isLoading: false })
    }
  },
  refetch: async () => {
    // Fetch current user data
    try {
      const response = await fetch("/api/me", {
        credentials: "include",
      })
      if (response.ok) {
        const user = await response.json()
        set({ user, isLoading: false })
      } else {
        set({ user: null, isLoading: false })
      }
    } catch (error) {
      set({ user: null, isLoading: false })
    }
  },
}))
