import { useRef } from "react"
import { toast } from "sonner"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAvatarSrc } from "@/hooks/use-auth"
import { useDeleteAvatar, useUploadAvatar } from "@/lib/api/hooks/profile"
import { useAuthStore } from "@/lib/auth"
import { ACCEPTED_TYPES, MIN_DIMENSION, validateAvatarFile } from "@/lib/avatar-validation"

export function AvatarSection() {
  const user = useAuthStore((state) => state.user)
  const avatarSrc = useAvatarSrc()
  const upload = useUploadAvatar()
  const remove = useDeleteAvatar()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const displayName = user?.name || user?.username || "Account"
  const initials = displayName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)

  const isBusy = upload.isPending || remove.isPending

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    // Reset the input so selecting the same file again still fires onChange.
    event.target.value = ""
    if (!file) {
      return
    }
    const error = await validateAvatarFile(file)
    if (error) {
      toast.error(error)
      return
    }
    upload.mutate(file)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile picture</CardTitle>
        <CardDescription>
          Upload an image to personalize your account. JPEG, PNG, or WebP, at least {MIN_DIMENSION}×{MIN_DIMENSION} pixels and up to 2 MB.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex items-center gap-6">
        <Avatar className="h-20 w-20">
          <AvatarImage src={avatarSrc} alt={displayName} />
          <AvatarFallback className="text-lg">{initials}</AvatarFallback>
        </Avatar>
        <div className="flex flex-wrap gap-2">
          <input ref={fileInputRef} type="file" accept={ACCEPTED_TYPES.join(",")} className="hidden" onChange={handleFileChange} />
          <Button onClick={() => fileInputRef.current?.click()} disabled={isBusy}>
            {user?.avatarUrl ? "Change picture" : "Upload picture"}
          </Button>
          {user?.avatarUrl && (
            <Button variant="outline" onClick={() => remove.mutate()} disabled={isBusy}>
              Remove
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
