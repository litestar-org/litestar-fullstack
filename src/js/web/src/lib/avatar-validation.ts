// Strict client-side avatar policy. The server (ProfileController) is the
// security boundary and accepts a broader set (JPEG/PNG/WebP/GIF up to 5 MB);
// these tighter rules are a deliberate UX gate: no animated GIF avatars, a
// smaller payload, and a minimum resolution so avatars don't render blurry.
export const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"]
export const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
export const MAX_AVATAR_SIZE = 2 * 1024 * 1024 // 2 MB
export const MIN_DIMENSION = 256 // px, width and height

/**
 * Read the pixel dimensions of an image file.
 *
 * Uses `createImageBitmap`, which decodes off the main thread and works with a
 * `File`/`Blob` directly. Returns `null` if the bytes can't be decoded as an
 * image (e.g. a renamed non-image file).
 */
async function readImageDimensions(file: File): Promise<{ width: number; height: number } | null> {
  try {
    const bitmap = await createImageBitmap(file)
    const { width, height } = bitmap
    bitmap.close()
    return { width, height }
  } catch {
    return null
  }
}

/**
 * Validate an avatar file before upload, strictly.
 *
 * Returns an error message to show the user, or `null` when the file is valid.
 * Client-side checks are a UX nicety only — the server re-validates magic bytes
 * and size, so this is never the security boundary.
 */
export async function validateAvatarFile(file: File): Promise<string | null> {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return "Please choose a JPEG, PNG, or WebP image."
  }
  const extension = file.name.split(".").pop()?.toLowerCase() ?? ""
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    return "The file extension does not match a supported image type."
  }
  if (file.size === 0) {
    return "The selected file is empty."
  }
  if (file.size > MAX_AVATAR_SIZE) {
    return "Image must be 2 MB or smaller."
  }
  const dimensions = await readImageDimensions(file)
  if (!dimensions) {
    return "Could not read the image. Please choose a different file."
  }
  if (dimensions.width < MIN_DIMENSION || dimensions.height < MIN_DIMENSION) {
    return `Image must be at least ${MIN_DIMENSION}×${MIN_DIMENSION} pixels.`
  }
  return null
}
