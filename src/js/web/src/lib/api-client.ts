import { getCsrfHeaderName, getCsrfToken } from "litestar-vite-plugin/helpers"
import { client } from "@/lib/generated/api/client.gen"
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from "@/lib/generated/routes"

export const UNSAFE_HTTP_METHODS: ReadonlySet<string> = new Set(["POST", "PUT", "PATCH", "DELETE"])

const PUBLIC_AUTH_PREFIXES = ["/login", "/signup", "/mfa-challenge", "/forgot-password", "/reset-password", "/verify-email", "/auth/"]

const CREDENTIAL_CHECK_PATH_FRAGMENTS = [
  "/api/access/login",
  "/api/access/step-up/",
  "/api/access/mfa/",
  "/api/access/passkeys/",
  "/api/access/password/change",
  "/api/me/password",
]

const REAUTHENTICATION_REQUIRED = "reauthentication_required"
const APPLICATION_ACCESS_REQUIRED = "application_access_required"

// The security library's own routes (register, password reset, password change) answer every
// rejection with this sentence, so the reason has to be explained by the form that sent the request.
const GENERIC_REJECTION_DETAIL = "The request is invalid."

export interface ApiClientConfigOptions {
  baseUrl?: string
  /** The session is missing or expired. */
  onUnauthorized?: () => void
  /** The session is valid, but the account lacks the role required to use the application. */
  onAccessDenied?: () => void
}

let isConfigured = false
let requestInterceptorId: number | null = null
let errorInterceptorId: number | null = null
let activeOnUnauthorized: (() => void) | undefined
let activeOnAccessDenied: (() => void) | undefined

function isPublicAuthPath(pathname: string): boolean {
  return PUBLIC_AUTH_PREFIXES.some((prefix) => pathname.startsWith(prefix))
}

function isCredentialCheckRequest(requestUrl: string): boolean {
  return CREDENTIAL_CHECK_PATH_FRAGMENTS.some((fragment) => requestUrl.includes(fragment))
}

function readNonEmptyString(source: object, key: string): string | undefined {
  const value: unknown = (source as Record<string, unknown>)[key]
  if (typeof value !== "string") {
    return undefined
  }
  return value.trim() || undefined
}

/** Reads the machine-readable `code` member of a problem-details error body. */
function readProblemCode(error: unknown): string | undefined {
  if (typeof error !== "object" || error === null) {
    return undefined
  }
  return readNonEmptyString(error, "code")
}

export function extractApiErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === "string" && error.trim().length > 0) {
    return error
  }
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message
  }
  if (typeof error === "object" && error !== null) {
    return readNonEmptyString(error, "detail") ?? readNonEmptyString(error, "message") ?? readNonEmptyString(error, "title") ?? fallback
  }
  return fallback
}

/** True when the API refused a request without saying why. */
export function isGenericRejection(error: unknown): boolean {
  return typeof error === "object" && error !== null && readNonEmptyString(error, "detail") === GENERIC_REJECTION_DETAIL
}

export function isReauthenticationRequired(error: unknown): boolean {
  return readProblemCode(error) === REAUTHENTICATION_REQUIRED
}

export function isApplicationAccessRequired(error: unknown): boolean {
  return readProblemCode(error) === APPLICATION_ACCESS_REQUIRED
}

export function configureApiClient(options?: ApiClientConfigOptions): void {
  const baseUrl = options?.baseUrl ?? ""
  activeOnUnauthorized = options?.onUnauthorized
  activeOnAccessDenied = options?.onAccessDenied

  client.setConfig({
    baseUrl,
    credentials: "include",
  })

  if (isConfigured) {
    return
  }

  requestInterceptorId = client.interceptors.request.use((request) => {
    const method = request.method?.toUpperCase()
    if (method && UNSAFE_HTTP_METHODS.has(method)) {
      const token = getCsrfToken({ cookieName: CSRF_COOKIE_NAME })
      if (token) {
        const headerName = getCsrfHeaderName(CSRF_HEADER_NAME)
        request.headers.set(headerName, token)
      }
    }
    return request
  })

  errorInterceptorId = client.interceptors.error.use((error, response, request) => {
    if (response?.status === 401) {
      const requestUrl = request?.url ?? ""
      const pathname = typeof window !== "undefined" ? window.location.pathname : "/"
      if (!isCredentialCheckRequest(requestUrl) && !isPublicAuthPath(pathname)) {
        activeOnUnauthorized?.()
      }
    }
    if (response?.status === 403 && isApplicationAccessRequired(error)) {
      activeOnAccessDenied?.()
    }
    return error
  })

  isConfigured = true
}

export function resetApiClientForTest(): void {
  if (requestInterceptorId !== null) {
    client.interceptors.request.eject(requestInterceptorId)
    requestInterceptorId = null
  }
  if (errorInterceptorId !== null) {
    client.interceptors.error.eject(errorInterceptorId)
    errorInterceptorId = null
  }
  activeOnUnauthorized = undefined
  activeOnAccessDenied = undefined
  isConfigured = false
}
