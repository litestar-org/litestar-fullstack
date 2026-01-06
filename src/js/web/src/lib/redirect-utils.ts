/**
 * Redirect URL utilities for secure auth flow redirects.
 *
 * These utilities prevent open redirect vulnerabilities by validating
 * that redirect URLs are relative paths within the application.
 */

/**
 * Default redirect destination after authentication.
 */
export const DEFAULT_AUTH_REDIRECT = "/home"

/**
 * Validates and sanitizes redirect URLs to prevent open redirect vulnerabilities.
 * Only allows relative paths that start with '/'.
 *
 * @param url - The redirect URL to validate
 * @returns The validated URL if safe, or null if invalid/unsafe
 */
export function validateRedirectUrl(url: string | null | undefined): string | null {
  if (!url) return null

  // Must start with / (relative path)
  if (!url.startsWith("/")) return null

  // Prevent protocol-relative URLs (//evil.com)
  if (url.startsWith("//")) return null

  // Prevent javascript: and other dangerous protocols that might sneak in
  const lowercaseUrl = url.toLowerCase()
  if (lowercaseUrl.includes("javascript:")) return null
  if (lowercaseUrl.includes("data:")) return null
  if (lowercaseUrl.includes("vbscript:")) return null

  // Parse and ensure it's a valid path
  try {
    const parsed = new URL(url, window.location.origin)
    // Ensure the host matches our origin (in case of any URL parsing tricks)
    if (parsed.origin !== window.location.origin) return null
    // Return just the pathname + search + hash
    return parsed.pathname + parsed.search + parsed.hash
  } catch {
    return null
  }
}

/**
 * Gets the safe redirect URL, falling back to default if invalid.
 *
 * @param url - The redirect URL to validate
 * @param fallback - The fallback URL if validation fails (defaults to DEFAULT_AUTH_REDIRECT)
 * @returns The validated redirect URL or the fallback
 */
export function getSafeRedirectUrl(url: string | null | undefined, fallback: string = DEFAULT_AUTH_REDIRECT): string {
  return validateRedirectUrl(url) ?? fallback
}

/**
 * Builds a URL with a redirect search parameter.
 *
 * @param basePath - The base path (e.g., "/login")
 * @param redirectTo - The URL to redirect to after the base action
 * @returns The base path with redirect parameter, or just the base path if redirectTo is invalid
 */
export function buildRedirectUrl(basePath: string, redirectTo: string | null | undefined): string {
  const validated = validateRedirectUrl(redirectTo)
  if (!validated) return basePath
  return `${basePath}?redirect=${encodeURIComponent(validated)}`
}
