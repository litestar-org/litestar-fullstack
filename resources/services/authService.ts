import axios from "axios";

const API_URL = import.meta.env.VITE_APP_URL || "";

export const registerUserService = async (data: any) => {
  try {
    const response = await axios.post(`${API_URL}/api/access/signup`, data);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const loginUserService = async (data: any) => {
  try {
    const response = await axios.post(`${API_URL}/api/access/login`, data);
    return response.data;
  } catch (error) {
    throw error;
  }
};
