import api from "./api";
import type { IExplainer } from "../types/explainer";

export const getExplainers = async (
  runId: string = "",
): Promise<IExplainer[]> => {
  const params = runId !== "" ? { run_id: runId } : {};
  const response = await api.get<IExplainer[]>("/v1/explainer/", { params });
  return response.data;
};

export const createExplainer = async (
  name: string,
  runId: number,
  datasetId: number,
  explainerName: string,
  parameters: object,
): Promise<IExplainer> => {
  const data = {
    name,
    run_id: runId,
    dataset_id: datasetId,
    explainer_name: explainerName,
    parameters,
  };

  const response = await api.post<IExplainer>("/v1/explainer", data);
  return response.data;
};
