import { AxiosInstance } from "axios"
import { useAuth } from "@/composables/useAuth"
import { routerPush } from "@/router"
import { useAppStore } from "@/stores/app"
export function configureAuthorizationHeaderInterceptor(axiosInstance: AxiosInstance, prefix = "Bearer") {
  axiosInstance.interceptors.request.use((config) => {
    const auth = useAuth()

    config.headers = config.headers ?? {}
    if (auth.isAuthenticated) {
      config.headers.Authorization = `${prefix} ${auth.currentAuth.accessToken}`
    }
    return config
  })
  axiosInstance.interceptors.response.use(
    (response) => {
      return response
    },
    async (error) => {
      const auth = useAuth()
      const originalConfig = error.config
      const appStore = useAppStore()
      const authenticationErrorResponses = new Set([401, 403])
      const safeUrls = new Set(["/api/account/login/access-token", "/api/account/login/refresh-token"])
      if (!safeUrls.has(originalConfig.url) && error.response) {
        // Access Token was expired
        if (authenticationErrorResponses.has(error.response.status) && !originalConfig._retry) {
          originalConfig._retry = true
          try {
            await auth.refreshToken()
            return axiosInstance(originalConfig)
          } catch (_error) {
            console.log("clearing login")
            appStore.setAuth()
            routerPush("login")
          }
        }
        if (authenticationErrorResponses.has(error.response.status) && originalConfig._retry) {
          console.log("clearing login")
          appStore.setAuth()
          routerPush("login")
        }
      }
      return Promise.reject(error)
    }
  )
}
