import "pinia"
import ApplicationLogo from "@/components/ApplicationLogo.vue"
import CenteredLayout from "@/layouts/CenteredLayout.vue"
 import RouterViewTransition from "@/components/RouterViewTransition.vue"

import type { App } from "vue"

export default function registerGlobalComponents(app: App): void {
  app.component("ApplicationLogo", ApplicationLogo)
  app.component("CenteredLayout", CenteredLayout)
   app.component("RouterViewTransition", RouterViewTransition)
}
