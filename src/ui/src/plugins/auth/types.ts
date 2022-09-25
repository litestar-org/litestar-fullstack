import { AxiosInstance } from "axios"
import { RouteLocationRaw, Router, RouteRecordName } from "vue-router"
import { Auth } from "@/api/types"
import {
  AccountApiLoginRequest,
  AccountApiRegisterUserRequest,
  AccountApiRequestPasswordResetRequest,
  AccountApiRequestUserVerificationTokenRequest,
  AccountApiResetPasswordRequest,
  AccountApiUpdateUserPasswordRequest,
  AccountApiUpdateUserProfileRequest,
  AccountApiVerifyUserRequest,
  ErrorMessage,
  Message,
  Token,
  User,
} from "@/api/client"

export interface AuthPlugin {
  readonly isAuthenticated: boolean
  readonly currentUser: User
  readonly currentAuth: Auth
  readonly login: (values: AccountApiLoginRequest) => Promise<Token | ErrorMessage>
  readonly refreshToken: () => Promise<Token | ErrorMessage>
  readonly logout: () => Promise<void>
  readonly updatePassword: (values: AccountApiUpdateUserPasswordRequest) => Promise<Message | ErrorMessage>
  readonly updateProfile: (values: AccountApiUpdateUserProfileRequest) => Promise<User | ErrorMessage>
  readonly registerUser: (values: AccountApiRegisterUserRequest) => Promise<Message | ErrorMessage>
  readonly resetPassword: (values: AccountApiResetPasswordRequest) => Promise<Message | ErrorMessage>
  readonly verifyUser: (values: AccountApiVerifyUserRequest) => Promise<Message | ErrorMessage>
  readonly requestPasswordReset: (values: AccountApiRequestPasswordResetRequest) => Promise<Message | ErrorMessage>
  readonly requestUserVerification: (
    values: AccountApiRequestUserVerificationTokenRequest
  ) => Promise<Message | ErrorMessage>
}

export interface AuthAxiosConfig {
  instance: AxiosInstance
  autoAddAuthorizationHeader: boolean
  authorizationHeaderPrefix?: string
}

export interface RequiredAuthOptions {
  router: Router
  loginRouteName: RouteRecordName
  loginRedirectRoute: RouteLocationRaw
  logoutRedirectRoute: RouteLocationRaw
  autoConfigureNavigationGuards: boolean
  axios?: AuthAxiosConfig
}

/*
 * Make all optional but router
 * See: https://www.typescriptlang.org/docs/handbook/utility-types.html#partialtype
 * See: https://stackoverflow.com/a/51507473/4873750
 */
export interface AuthOptions extends Omit<Partial<RequiredAuthOptions>, "router"> {
  router: Router
}
