import axios from "axios";
import type { AxiosInstance } from "axios";

const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});
export default api;
