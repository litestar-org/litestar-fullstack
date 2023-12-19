import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL;

export const registerUserService = async (data: any) => {
  try {
    const response = await axios.post(`${API_URL}/api/v1/auth/register`, data);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const loginUserService = async (data: any) => {
  try {
    const response = await axios.post(`${API_URL}/api/v1/auth/login`, data);
    return response.data;
  } catch (error) {
    throw error;
  }
};
