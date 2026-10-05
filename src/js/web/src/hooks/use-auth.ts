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

/**
 * Resolve the current user's avatar URL for an `<img src>`.
 *
 * The backend versions the URL per upload, so a replaced image gets a new URL
 * and is never served stale from cache. Returns `undefined` when no avatar is
 * set so consumers fall back to initials.
 */
export function useAvatarSrc(): string | undefined {
  return useAuthStore((state) => state.user?.avatarUrl) ?? undefined
}
