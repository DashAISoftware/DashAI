import api from "./api";
import type { IExperiment } from "../../types/experiment";

export const getExperiments = async (): Promise<IExperiment[]> => {
  const response = await api.get<IExperiment[]>("experiment");
  return response.data;
};

export const getExperimentById = async (id: string): Promise<IExperiment> => {
  const response = await api.get<IExperiment>(`experiment/${id}`);
  return response.data;
};

export const createExperiment = async (formData: FormData): Promise<object> => {
  const response = await api.post<IExperiment>("experiment", formData);
  return response.data;
};

export const updateExperiment = async ({
  id,
  formData,
}: {
  id: string;
  formData: object;
}): Promise<object> => {
  const response = await api.patch(`experiment/${id}`, formData);
  return response.data;
};

export const deleteExperiment = async (id: string): Promise<object> => {
  const response = await api.delete(`experiment/${id}`);
  return response.data;
};
