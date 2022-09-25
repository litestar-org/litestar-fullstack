import { createApp } from "vue"
import App from "@/App.vue"
import { router } from "@/router"
import { createPinia } from "pinia"
import "@/assets/main.css"
import { createAuth } from "@/plugins/auth"
 import { createHead } from "@vueuse/head"
import registerGlobalComponents from "@/plugins/globalComponents"
 import Notifications from "notiwind"

export const app = createApp(App)
const head = createHead()

// Store setup (pinia)
const pinia = createPinia()
const auth = createAuth({
  router,
  // loginRouteName: "login",
  loginRedirectRoute: { name: "home" },
  logoutRedirectRoute: { name: "login" },
  autoConfigureNavigationGuards: true,
  axios: {
    instance: axiosInstance,
    autoAddAuthorizationHeader: true,
  },
})

// register global components
registerGlobalComponents(app)
app.use(head)
app.use(pinia)
app.use(router)
app.use(auth)
app.use(Notifications)

app.config.globalProperties.$http = axiosInstance
 app.provide("enable-route-transitions", true)
app.mount("#app")
