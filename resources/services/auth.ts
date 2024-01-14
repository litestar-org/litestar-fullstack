import axios from "axios"

const APP_URL = import.meta.env.APP_URL || ""

export const registerUserService = async (data: any) => {
  try {
    const response = await axios.post(`${APP_URL}/api/access/signup`, data)
    return response.data
  } catch (error) {
    throw error
  }
}

export const loginUserService = async (data: any) => {
  try {
    return await axios.post(`${APP_URL}/api/access/login`, data, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
  } catch (error) {
    throw error
  }
}
