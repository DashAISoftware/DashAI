import api from "./api";
import type { IArtifact } from "../types/artifact";
import type { IExplorer } from "../types/explorer";

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

// New: Create an explorer for a notebook (not exploration)
export const createNotebookExplorer = async (
  notebookId: number,
  columns: object[],
  explorationType: string,
  parameters: object,
  name?: string,
): Promise<IExplorer> => {
  const data: Record<string, any> = {
    notebook_id: notebookId,
    columns,
    exploration_type: explorationType,
    parameters,
  };
  if (name) data.name = name;
  const response = await api.post<IExplorer>(`${explorerEndpoint}`, data);
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
): Promise<IArtifact[]> => {
  const data = { options };
  const response = await api.post(
    `${explorerEndpoint}/${explorerId}/results/`,
    data,
  );
  return response.data;
};

export const updateExplorerResults = async (
  explorerId: number,
  index: number,
  figure: unknown,
): Promise<{ message: string }> => {
  const response = await api.put(`${explorerEndpoint}/${explorerId}/results/`, {
    index,
    figure,
  });
  return response.data;
};

export const resetExplorerResults = async (
  explorerId: number,
  index: number,
): Promise<{ message: string }> => {
  const response = await api.delete(
    `${explorerEndpoint}/${explorerId}/results/override/${index}`,
  );
  return response.data;
};
