import axios from "axios"
import { API } from "@/types/api"
const APP_URL = import.meta.env.APP_URL || ""
export const getUserProfileService = async (data: any) => {
  try {
    const response = await axios.post<API.AccountProfile.Http200.ResponseBody>(
      `${APP_URL}/api/access/signup`,
      data
    )
    return response.data
  } catch (error) {
    throw error
  }
}
