import api from "./api";
import type { IExplorer } from "../types/explorer";

const explorerEndpoint = "/v1/explorer";

export const getExplorers = async (): Promise<IExplorer[]> => {
  const response = await api.get<IExplorer[]>(`${explorerEndpoint}/`);
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

export const getExplorersByDatasetId = async (
  datasetId: number,
): Promise<IExplorer[]> => {
  const response = await api.get<IExplorer[]>(
    `${explorerEndpoint}/dataset/${datasetId}/`,
  );
  return response.data;
};

export const createExplorer = async (
  datasetId: number,
  columns: object,
  explorationType: string,
  parameters: object,
  name: string,
): Promise<IExplorer> => {
  const data = {
    dataset_id: datasetId,
    columns,
    exploration_type: explorationType,
    parameters,
    name,
  };
  const response = await api.post<IExplorer>(explorerEndpoint, data);
  return response.data;
};

export const deleteExplorer = async (explorerId: string): Promise<object> => {
  const response = await api.delete(`${explorerEndpoint}/${explorerId}/`);
  return response.data;
};

export const getExplorerResults = async (
  explorerId: number,
): Promise<object> => {
  const response = await api.get(`${explorerEndpoint}/${explorerId}/results/`);
  return response.data;
};
