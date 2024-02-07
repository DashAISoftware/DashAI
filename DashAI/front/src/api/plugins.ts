import api from "./api";
import type { IPlugin } from "../types/plugin";

const endpointURL = "/v1/plugins";

export const getPlugins = async (): Promise<IPlugin[]> => {
  const response = await api.get<IPlugin[]>(endpointURL);
  return response.data;
};
