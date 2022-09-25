import { App, computed, reactive, readonly } from "vue"
import { setupDevtools } from "./devtools"
import { configureAuthorizationHeaderInterceptor } from "./interceptors"
import { configureNavigationGuards } from "./navigationGuards"
import { AuthOptions, AuthPlugin, RequiredAuthOptions } from "./types"
import { useAppStore } from "@/stores/app"
import { accountApi } from "@/api"
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
import { storeToRefs } from "pinia"
import axios, { AxiosResponse } from "axios"
import { BACKEND_UNAVAILABLE } from "@/api/types"

export let authInstance: AuthPlugin | undefined = undefined

function setupAuthPlugin(options: RequiredAuthOptions): AuthPlugin {
  const router = options.router
  const { auth: currentAuth, currentUser } = storeToRefs(useAppStore())
  const isAuthenticated = computed((): boolean => {
    return !!(currentAuth.value && currentAuth.value.accessToken && currentAuth.value.refreshToken)
  })
  async function login(params: AccountApiLoginRequest): Promise<Token | ErrorMessage> {
    const appStore = useAppStore()
    const result = await accountApi.login(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        router.push(router.currentRoute.value.query.redirectTo?.toString() || options.loginRedirectRoute)
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        router.push(router.currentRoute.value.query.redirectTo?.toString() || options.loginRedirectRoute)

        return BACKEND_UNAVAILABLE
      }
    } else {
      appStore.setAuth(result.data)
      router.push(router.currentRoute.value.query.redirectTo?.toString() || options.loginRedirectRoute)
      return result.data
    }
  }
  async function refreshToken(): Promise<Token | ErrorMessage> {
    const appStore = useAppStore()
    const result = await accountApi
      .refreshAccessToken({ refreshToken: currentAuth.value.refreshToken })
      .catch((error) => {
        return error
      })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      appStore.setAuth(result.data)
      return result.data as Token
    }
  }
  async function logout() {
    const appStore = useAppStore()
    appStore.setAuth()
    router.push(options.logoutRedirectRoute)
  }
  async function updateProfile(params: AccountApiUpdateUserProfileRequest): Promise<User | ErrorMessage> {
    const appStore = useAppStore()
    const result = await accountApi.updateUserProfile(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      appStore.setCurrentUser(result.data)
      return result.data as User
    }
  }
  async function updatePassword(params: AccountApiUpdateUserPasswordRequest): Promise<Message | ErrorMessage> {
    const appStore = useAppStore()
    const result = await accountApi.updateUserPassword(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      appStore.setCurrentUser(result.data)
      return result.data as Message
    }
  }
  async function registerUser(params: AccountApiRegisterUserRequest): Promise<Message | ErrorMessage> {
    const result = await accountApi.registerUser(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      return result.data as Message
    }
  }
  async function resetPassword(params: AccountApiResetPasswordRequest): Promise<Message | ErrorMessage> {
    const result = await accountApi.resetPassword(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      return result.data as Message
    }
  }
  async function verifyUser(params: AccountApiVerifyUserRequest): Promise<Message | ErrorMessage> {
    const result = await accountApi.verifyUser(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      return result.data as Message
    }
  }
  async function requestPasswordReset(params: AccountApiRequestPasswordResetRequest): Promise<Message | ErrorMessage> {
    const result = await accountApi.requestPasswordReset(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      return result.data as Message
    }
  }
  async function requestUserVerification(
    params: AccountApiRequestUserVerificationTokenRequest
  ): Promise<Message | ErrorMessage> {
    const result = await accountApi.requestUserVerificationToken(params).catch((error) => {
      return error
    })
    if (result instanceof Error) {
      if (axios.isAxiosError(result)) {
        return (result.response as AxiosResponse<ErrorMessage>)?.data || BACKEND_UNAVAILABLE
      } else {
        return BACKEND_UNAVAILABLE
      }
    } else {
      return result.data as Message
    }
  }
  /*
   * "reactive" unwraps 'ref's, therefore using the .value is not required.
   * E.g: from "auth.isAuthenticated.value" to "auth.isAuthenticated"
   * but when using destructuring like: { isAuthenticated } = useAuth() the reactivity over isAuthenticated would be lost
   * this is not recommended but in such case use toRefs: { isAuthenticated } = toRefs(useAuth())
   * See: https://v3.vuejs.org/guide/reactivity-fundamentals.html#ref-unwrapping
   * And: https://v3.vuejs.org/guide/reactivity-fundamentals.html#destructuring-reactive-state
   */
  const unWrappedRefs = reactive({
    isAuthenticated,
    currentAuth,
    currentUser,
    login,
    logout,
    refreshToken,
    registerUser,
    updateProfile,
    updatePassword,
    resetPassword,
    verifyUser,
    requestPasswordReset,
    requestUserVerification,
  })

  return readonly(unWrappedRefs)
}

const defaultOptions = {
  loginRedirectRoute: "/",
  logoutRedirectRoute: "/",
  loginRouteName: "login",
  autoConfigureNavigationGuards: true,
}
export function createAuth(appOptions: AuthOptions) {
  // Fill default params to options that were not received
  const options: RequiredAuthOptions = { ...defaultOptions, ...appOptions }

  return {
    install: (app: App): void => {
      authInstance = setupAuthPlugin(options)
      app.config.globalProperties.$auth = authInstance

      if (options.autoConfigureNavigationGuards) {
        configureNavigationGuards(options.router, options)
      }

      if (options.axios?.autoAddAuthorizationHeader) {
        configureAuthorizationHeaderInterceptor(options.axios.instance, options.axios.authorizationHeaderPrefix)
      }

      if (import.meta.env.DEV) {
        setupDevtools(app, authInstance)
      }
    },
  }
}
