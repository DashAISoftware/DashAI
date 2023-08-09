import api from "./api";
import type { IRun } from "../types/run";

export const getRuns = async (experimentId: string = ""): Promise<IRun[]> => {
  const params = experimentId !== "" ? { experiment_id: experimentId } : {};
  const response = await api.get<IRun[]>("/v1/run/", { params });
  return response.data;
};

export const getRunById = async (runId: string): Promise<IRun> => {
  const response = await api.get<IRun>(`/v1/run/${runId}`);
  return response.data;
};

export const createRun = async (
  experimentId: string,
  modelName: string,
  name: string,
  parameters: object,
  description: string,
): Promise<IRun> => {
  const formData = new FormData();

  formData.append(
    "params",
    JSON.stringify({
      experiment_id: experimentId,
      model_name: modelName,
      name,
      parameters,
      description,
    }),
  );
  const response = await api.post<IRun>("/v1/run/", formData);
  return response.data;
};
