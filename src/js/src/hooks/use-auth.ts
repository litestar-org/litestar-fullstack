import { useAuthStore } from "@/lib/auth"

export function useAuth() {
  const { user, logout, checkAuth, isLoading, isAuthenticated } = useAuthStore()

  return {
    user,
    logout,
    refetch: checkAuth,
    isLoading,
    isAuthenticated,
  }
}
