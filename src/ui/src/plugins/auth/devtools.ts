import { App, setupDevtoolsPlugin } from "@vue/devtools-api"
import { watch } from "vue"
import { AuthPlugin } from "./types"

const stateType = "Auth Plugin"

export function setupDevtools(app: App, plugin: AuthPlugin) {
  setupDevtoolsPlugin(
    {
      id: "basic-auth-plugin",
      label: "Basic Auth Plugin",
      componentStateTypes: [stateType],
      app,
    },
    (api) => {
      api.on.inspectComponent((payload) => {
        payload.instanceData.state.push({
          type: stateType,
          key: "$auth",
          value: plugin,
        })
      })

      watch(plugin, () => {
        api.notifyComponentUpdate()
      })
    }
  )
}
