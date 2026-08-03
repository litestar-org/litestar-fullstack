import { useMutation } from "@tanstack/react-query"
import { toast } from "sonner"
import { useAuthStore } from "@/lib/auth"
import { accountAvatarDelete, accountAvatarUpload } from "@/lib/generated/api"

/**
 * Upload (or replace) the current user's avatar.
 *
 * The backend returns the updated `User`, so we push it straight into the auth
 * store and bump the avatar version to defeat image caching at the stable URL.
 */
export function useUploadAvatar() {
  const setUser = useAuthStore((state) => state.setUser)
  const bumpAvatarVersion = useAuthStore((state) => state.bumpAvatarVersion)

  return useMutation({
    mutationFn: async (file: File) => {
      const { data } = await accountAvatarUpload({
        body: { file },
        throwOnError: true,
      })
      return data
    },
    onSuccess: (user) => {
      setUser(user)
      bumpAvatarVersion()
      toast.success("Avatar updated")
    },
    onError: (error) => {
      toast.error("Could not upload avatar", {
        description: error instanceof Error ? error.message : "Try again later",
      })
    },
  })
}

/**
 * Remove the current user's avatar.
 *
 * The delete endpoint returns 204 with no body, so we clear `avatarUrl` on the
 * cached user locally rather than refetching the whole profile.
 */
export function useDeleteAvatar() {
  const setUser = useAuthStore((state) => state.setUser)
  const bumpAvatarVersion = useAuthStore((state) => state.bumpAvatarVersion)

  return useMutation({
    mutationFn: async () => {
      await accountAvatarDelete({ throwOnError: true })
    },
    onSuccess: () => {
      const currentUser = useAuthStore.getState().user
      if (currentUser) {
        setUser({ ...currentUser, avatarUrl: null })
      }
      bumpAvatarVersion()
      toast.success("Avatar removed")
    },
    onError: (error) => {
      toast.error("Could not remove avatar", {
        description: error instanceof Error ? error.message : "Try again later",
      })
    },
  })
}
