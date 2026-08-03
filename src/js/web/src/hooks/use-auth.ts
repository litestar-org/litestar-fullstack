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
 * Resolve the current user's avatar URL with a cache-busting version param.
 *
 * The avatar is served from a stable URL, so without the version suffix the
 * browser would keep showing a stale image after the user replaces it.
 * Returns `undefined` when no avatar is set so consumers fall back to initials.
 */
export function useAvatarSrc(): string | undefined {
  const avatarUrl = useAuthStore((state) => state.user?.avatarUrl)
  const avatarVersion = useAuthStore((state) => state.avatarVersion)

  if (!avatarUrl) {
    return undefined
  }
  return `${avatarUrl}?v=${avatarVersion}`
}
