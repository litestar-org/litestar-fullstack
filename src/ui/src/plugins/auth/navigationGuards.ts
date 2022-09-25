import { RouteLocationRaw, Router } from "vue-router"
import { RequiredAuthOptions } from "@/plugins/auth/types"
import { useAuth } from "@/composables/useAuth"

export function configureNavigationGuards(router: Router, options: RequiredAuthOptions) {
  router.beforeEach(async (to): Promise<boolean | RouteLocationRaw> => {
    const auth = useAuth()
    // if (!auth.isAuthenticated) {
    //   await auth.logout()
    // }
    if (to.name === options.loginRouteName) {
      if (auth.isAuthenticated) {
        console.log("already authenticated")
        return options.loginRedirectRoute
      }
      return true
    }

    if (!to.meta.public || to.meta.requiresAuth) {
      if (!auth.isAuthenticated) {
        return { name: options.loginRouteName, query: { redirectTo: to.fullPath } }
      }
    }

    return true
  })
}
