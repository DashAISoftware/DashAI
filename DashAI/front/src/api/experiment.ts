import api from "./api";
import type { IExperiment } from "../types/experiment";

const endpointURL = "/v1/experiment";

export const getExperiments = async (): Promise<IExperiment[]> => {
  const response = await api.get<IExperiment[]>(endpointURL);
  return response.data;
};

export const getExperimentById = async (id: string): Promise<IExperiment> => {
  const response = await api.get<IExperiment>(`${endpointURL}/${id}`);
  return response.data;
};

export const createExperiment = async (
  datasetId: number,
  taskName: string,
  name: string,
): Promise<IExperiment> => {
  const formData = new FormData();

  formData.append(
    "params",
    JSON.stringify({
      dataset_id: datasetId,
      task_name: taskName,
      name,
    }),
  );

  const response = await api.post<IExperiment>("/v1/experiment/", formData);
  return response.data;
};

export const updateExperiment = async ({
  id,
  formData,
}: {
  id: string;
  formData: object;
}): Promise<object> => {
  const response = await api.patch(`/v1/experiment/${id}`, formData);
  return response.data;
};

export const deleteExperiment = async (id: string): Promise<object> => {
  const response = await api.delete(`/v1/experiment/${id}`);
  return response.data;
};
