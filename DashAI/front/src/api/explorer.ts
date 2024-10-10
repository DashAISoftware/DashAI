import api from "./api";
import type { IExplorer, IExplorerResults } from "../types/explorer";

const explorerEndpoint = "/v1/explorer";

export const getExplorers = async (
  skip: number | null = null,
  limit: number | null = null,
): Promise<IExplorer[]> => {
  const rawparams = { skip, limit };
  const params = Object.fromEntries(
    Object.entries(rawparams).filter(([_, v]) => v !== null),
  );

  const response = await api.get<IExplorer[]>(`${explorerEndpoint}/`, {
    params,
  });
  return response.data;
};

export const getExplorerById = async (
  explorerId: number,
): Promise<IExplorer> => {
  const response = await api.get<IExplorer>(
    `${explorerEndpoint}/${explorerId}/`,
  );
  return response.data;
};

export const getExplorersByExplorationId = async (
  explorationId: number,
  skip: number | null = null,
  limit: number | null = null,
): Promise<IExplorer[]> => {
  const rawparams = { skip, limit };
  const params = Object.fromEntries(
    Object.entries(rawparams).filter(([_, v]) => v !== null),
  );

  const response = await api.get<IExplorer[]>(
    `${explorerEndpoint}/exploration/${explorationId}/`,
    { params },
  );
  return response.data;
};

export const createExplorer = async (
  explorationId: number,
  columns: object,
  explorationType: string,
  parameters: object,
  name: string,
): Promise<IExplorer> => {
  const data = {
    exploration_id: explorationId,
    columns,
    exploration_type: explorationType,
    parameters,
    name,
  };
  const response = await api.post<IExplorer>(explorerEndpoint, data);
  return response.data;
};

export const updateExplorer = async (
  explorerId: string,
  columns: object,
  parameters: object,
  name: string,
): Promise<IExplorer> => {
  const data = { columns, parameters, name };
  const response = await api.patch<IExplorer>(
    `${explorerEndpoint}/${explorerId}/`,
    data,
  );
  return response.data;
};

export const deleteExplorer = async (explorerId: string): Promise<object> => {
  const response = await api.delete(`${explorerEndpoint}/${explorerId}/`);
  return response.data;
};

export const getExplorerResults = async (
  explorerId: number,
  options: object = {},
): Promise<IExplorerResults> => {
  const data = { options };
  const response = await api.post(
    `${explorerEndpoint}/${explorerId}/results/`,
    data,
  );
  return response.data;
};
