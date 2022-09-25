import { AccountApi, TagsApi, UsersApi, EnvironmentsApi, ErrorMessage } from "@/api/client"
import axiosInstance from "@/api/axios"
import { SITE_URL } from "@/api/config"
export const accountApi = new AccountApi(undefined, SITE_URL, axiosInstance)
export const tagApi = new TagsApi(undefined, SITE_URL, axiosInstance)
export const userApi = new UsersApi(undefined, SITE_URL, axiosInstance)
export const environmentApi = new EnvironmentsApi(undefined, SITE_URL, axiosInstance)

export function isApiError(object: any): object is ErrorMessage | undefined {
  if ("error" in object) {
    return true
  } else if (object === undefined) {
    return true
  } else {
    return false
  }
}
