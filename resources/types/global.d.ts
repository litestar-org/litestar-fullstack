import { AxiosInstance } from "axios"
import { route as litestarRoute } from "litestar-vite-plugin/inertia-helpers"
import type { Page, PageProps, Errors, ErrorBag } from "@inertiajs/core"
import { AuthData, Flash } from "."
declare global {
  interface Window {
    axios: AxiosInstance
  }

  var route: typeof litestarRoute

  interface InertiaProps extends Page<PageProps> {
    errors?: Errors & ErrorBag
    auth?: AuthData
    csrf_token?: string
    flash?: Flash[]
    [key: string]: any
  }
}
