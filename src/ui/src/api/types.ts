import {
   User,
 
  Users,
 
  ErrorMessage,
 
 
} from "@/api/client"
import { ComputedRef, reactive } from "vue"

export const ANONYMOUS_USER: Readonly<User> = Object.freeze({
  id: 0,
  email: "",
  fullName: "Anonymous",
  isSuperuser: false,
  isActive: false,
  isVerified: false,
}) 
 
export const NO_TEAM: Readonly<Team> = Object.freeze({
  id: 0,
  slug: "no-team",
  name: "No Team",
  uploads: [],
})
const paginatedResults = Object.freeze({
  count: 0,
  limit: 10,
  skip: 0,
  results: [],
})
export const DEFAULT_TEAMS: Readonly<Teams> = paginatedResults
export const DEFAULT_USERS: Readonly<Users> = paginatedResults

export const notification = reactive({
  id: 0,
  group: "",
  message: "",
  messageType: "info",
  timeout: 3000,
})
export interface Auth {
  accessToken: string
    tokenType: string
  userId: string | null
  authenticatedAt: Date | null
  accessTokenValidUntil: Date | null
}
export const ANONYMOUS_AUTH: Readonly<Auth> = Object.freeze({
  userId: "",
  accessToken: "",
   tokenType: "",
  authenticatedAt: null,
  accessTokenValidUntil: null,
}) 

export interface JwtOptions<Fallback> {
  /**
   * Value returned when encounter error on decoding
   *
   * @default null
   */
  fallbackValue?: Fallback
  /**
   * Error callback for decoding
   */
  onError?: (error: unknown) => void
}
export interface JwtResult<Payload, Header, Fallback> {
  header: ComputedRef<Header | Fallback>
  payload: ComputedRef<Payload | Fallback>
}
 
export const BACKEND_UNAVAILABLE: Readonly<ErrorMessage> = Object.freeze({
  error: {
    code: 500,
    message: "Backend unavailable",
    status: "error",
  },
})
