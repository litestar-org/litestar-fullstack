import { AxiosInstance } from "axios"
import { route as litestarRoute } from "litestar-vite-plugin/inertia-helpers"

declare global {
  interface Window {
    axios: AxiosInstance
  }

  var route: typeof litestarRoute
}
