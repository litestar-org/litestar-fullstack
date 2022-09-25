import { createRouter, createWebHashHistory, RouteParams } from "vue-router"
import Index from "@/pages/home/Index.vue"
// import { useAccountStore } from "@/stores/account"
declare module "vue-router" {
  interface RouteMeta {
    requiresAuth: boolean
    activeTab?: string
    activeSubTab?: string
    layout?: string
    transition?: string
    requiresMembership?: boolean
    requiresAdmin?: boolean
    requiresSuperuser?: boolean
    public?: boolean
  }
}
export type AppRouteNames =
  | "home"
  | "login"
  | "register"
  | "profile"
  | "verify"
  | "request-password-reset"
  | "reset-password"
  | "settings"
  | "users"
  | "user-detail"
  | "add-user"
  | "environments"
  | "environment-config"
  | "environment-detail"
  | "offload"
  | "present"
  | "prepare"
  | "schedule"
  | "add-environment"
  | "tags"
  | "tag-detail"
  | "add-tag"
  | "page-not-found"
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      name: "home",
      path: "/",
      component: Index,
      meta: {
        requiresAuth: true,
        activeTab: "home",
      },
    },

    {
      name: "login",
      path: "/login",
      component: () => import("@/pages/access/Login.vue"),
      meta: {
        requiresAuth: false,
      },
    },

    {
      name: "register",
      path: "/register",
      component: () => import("@/pages/access/Register.vue"),
      meta: {
        requiresAuth: false,
      },
    },
    {
      name: "request-password-reset",
      path: "/reset-password",
      component: () => import("@/pages/access/RequestPasswordReset.vue"),
      meta: {
        requiresAuth: false,
      },
    },
    {
      name: "reset-password",
      path: "/reset-password/:token",
      component: () => import("@/pages/access/ResetPassword.vue"),
      meta: {
        requiresAuth: false,
      },
    },
    {
      name: "verify",
      path: "/verify/:token",
      component: () => import("@/pages/access/Verify.vue"),
      meta: {
        requiresAuth: false,
      },
    },
    {
      name: "profile",
      path: "/profile",
      component: () => import("@/pages/profile/Index.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "settings",
      },
    },

    {
      name: "settings",
      path: "/settings",
      component: () => import("@/pages/settings/Index.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "settings",
      },
    },
    {
      name: "tags",
      path: "/settings/tags",
      component: () => import("@/pages/settings/tags/Index.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "settings",
      },
    },
    {
      name: "add-tag",
      path: "/settings/tags/add",
      component: () => import("@/pages/settings/tags/Add.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "settings",
      },
    },
    {
      name: "tag-detail",
      path: "/settings/tags/:tagSlug",
      component: () => import("@/pages/settings/tags/Detail.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "settings",
      },
    },
    {
      name: "system-config",
      path: "/settings/config",
      component: () => import("@/pages/settings/system/Index.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "settings",
      },
    },
    {
      name: "users",
      path: "/settings/users",
      component: () => import("@/pages/settings/users/Index.vue"),
      meta: {
        requiresAuth: true,
        requiresAdmin: true,
        activeTab: "settings",
      },
    },
    {
      name: "environments",
      path: "/environments",
      component: () => import("@/pages/environments/Index.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "environments",
      },
    },

    {
      name: "add-environment",
      path: "/environments/add",
      component: () => import("@/pages/environments/Add.vue"),
      meta: {
        requiresAuth: true,
        activeTab: "environments",
      },
    },
    {
      name: "environment-detail",
      path: "/environments/:environmentSlug",
      component: () => import("@/pages/environments/Details.vue"),
      meta: {
        requiresAuth: true,
        activeSubTab: "dashboard",
        //activeTab: "environments",
      },
    },
    {
      name: "environment-config",
      path: "/environments/:environmentSlug/config",
      component: () => import("@/pages/environments/Configure.vue"),
      meta: {
        requiresAuth: true,
        //activeTab: "environments",
        activeSubTab: "configure",
      },
    },
    {
      name: "prepare",
      path: "/environments/:environmentSlug/prepare",
      component: () => import("@/pages/environments/Prepare.vue"),
      meta: {
        requiresAuth: true,
        //activeTab: "environments",
        activeSubTab: "prepare",
      },
    },
    {
      name: "offload",
      path: "/environments/:environmentSlug/offload",
      component: () => import("@/pages/environments/Offload.vue"),
      meta: {
        requiresAuth: true,
        //activeTab: "environments",
        activeSubTab: "offload",
      },
    },
    {
      name: "present",
      path: "/environments/:environmentSlug/present",
      component: () => import("@/pages/environments/Present.vue"),
      meta: {
        requiresAuth: true,
        //activeTab: "environments",
        activeSubTab: "present",
      },
    },
    {
      name: "schedule",
      path: "/environments/:environmentSlug/schedule",
      component: () => import("@/pages/environments/Schedule.vue"),
      meta: {
        requiresAuth: true,
        //activeTab: "environments",
        activeSubTab: "schedule",
      },
    },
    /* make sure this route is last */
    {
      name: "page-not-found",
      path: "/:pathMatch(.*)*",
      component: () => import("@/pages/404.vue"),
      meta: {
        requiresAuth: false,
      },
    },
  ],
})

export function routerPush(name: AppRouteNames, params?: RouteParams): ReturnType<typeof router.push> {
  if (params !== undefined) {
    return router.push({
      name,
      params,
    })
  } else {
    return router.push({ name })
  }
}

// router.beforeEach((to, from, next) => {
//   // Not logged into a guarded route?
//   const accountStore = useAccountStore()
//   const currentTime = new Date()

//   if (accountStore.auth.refreshTokenValidUntil && accountStore.auth.refreshTokenValidUntil < currentTime) {
//     console.log("clearing login")
//     accountStore.clearLogin()
//   }
//   if (accountStore.auth.accessTokenValidUntil && accountStore.auth.accessTokenValidUntil < currentTime) {
//     accountStore.refreshAccessToken()
//   }
//   if (accountStore.isAuthenticated === false && to.meta.requiresAuth === true) {
//     console.log("requires auth, redirect to login")

//     next({
//       name: "login",
//       query: {
//         redirect: to.fullPath,
//       },
//     })
//   }

//   // Redirect user to route if they don't have the correct subscription
//   // else if ( to.meta.requiresAuth === true && !user?.value?.subscription  && to.name!.toString().startsWith('subscribe') === false ) {
//   //   console.log('requires valid subscription, redirect to subscribe');
//   //   next({ name: 'subscribe' })
//   // }

//   // Logged in for an auth route
//   else if ((to.name == "login" || to.name == "register") && accountStore.isAuthenticated === true) {
//     console.log("User already logged in.  Redirecting to home.")

//     next({ name: "home" })
//   }

//   // Carry On...
//   else next()
// })
