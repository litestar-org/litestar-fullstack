import { AxiosInstance } from "axios"
import type { Page, PageProps, Errors, ErrorBag } from "@inertiajs/core"
import { AuthData, FlashMessages } from "."
declare global {
  interface Window {
    axios: AxiosInstance
  }

  interface InertiaProps extends Page<PageProps> {
    errors?: Errors & ErrorBag
    auth?: AuthData
    csrf_token?: string
    flash?: FlashMessages
    [key: string]: any
  }
}
