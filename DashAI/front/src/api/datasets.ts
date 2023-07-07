import api from "./api";
import type { IDataset } from "../types/dataset";

const datasetEndpoint = "/v1/dataset";

export const uploadDataset = async (formData: object): Promise<object> => {
  const response = await api.post<IDataset[]>(datasetEndpoint, formData);
  return response.data;
};

export const getDatasets = async (): Promise<IDataset[]> => {
  const response = await api.get<IDataset[]>(datasetEndpoint);
  return response.data;
};

export const updateDataset = async (
  id: number,
  name: string | undefined,
  taskName: string | undefined,
): Promise<IDataset> => {
  let url = `${datasetEndpoint}/${id}`;
  if (name !== undefined) {
    url = `${url}?name=${name}`;
  }
  if (taskName !== undefined) {
    url = `${url}${name !== undefined ? "&" : "?"}task_name=${taskName}`;
  }
  const response = await api.patch<IDataset>(url);
  return response.data;
};

export const deleteDataset = async (id: string): Promise<object> => {
  const response = await api.delete(`${datasetEndpoint}/${id}`);
  return response.data;
};
