import api from "./api";
import type { IPlugin, PluginStatus } from "../types/plugin";

const endpointURL = "/v1/plugin";

export const getPlugins = async (): Promise<IPlugin[]> => {
  const response = await api.post<IPlugin[]>(`${endpointURL}/index`);
  return response.data;
};

export const getPluginById = async (pluginId: string): Promise<IPlugin> => {
  const response = await api.get<IPlugin>(`${endpointURL}/${pluginId}`);
  return response.data;
};

export const updatePlugin = async (
  pluginId: string,
  pluginStatus: PluginStatus,
): Promise<IPlugin> => {
  const data = { new_status: pluginStatus };
  const response = await api.patch<IPlugin>(`${endpointURL}/${pluginId}`, data);
  return response.data;
};

export const upgradePlugin = async (pluginId: string): Promise<IPlugin> => {
  const response = await api.patch<IPlugin>(
    `${endpointURL}/${pluginId}/upgrade`,
  );
  return response.data;
};
