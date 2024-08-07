import { AxiosInstance } from "axios"
import type { Page, PageProps, Errors, ErrorBag } from "@inertiajs/core"
import { AuthData, CurrentTeam, FlashMessages } from "."
declare global {
  interface Window {
    axios: AxiosInstance
  }

  interface InertiaProps extends Page<PageProps> {
    flash: FlashMessages
    errors: Errors & ErrorBag
    csrf_token: string
    auth?: AuthData
    currentTeam?: CurrentTeam
    [key: string]: any
  }
}
