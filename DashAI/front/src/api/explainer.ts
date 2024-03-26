import api from "./api";
import type { IExplainer } from "../types/explainer";

export const getExplainers = async (
  runId: string = "",
  scope: string = "",
): Promise<IExplainer[]> => {
  const params = runId !== "" ? { run_id: runId } : {};
  const response = await api.get<IExplainer[]>(`/v1/explainer/${scope}`, {
    params,
  });
  return response.data;
};

export const getExplainerPlot = async (
  explainerId: string = "",
  scope: string = "",
): Promise<IExplainer[]> => {
  const response = await api.get<IExplainer[]>(
    `/v1/explainer/${scope}/explanation/plot/${explainerId}`,
  );
  return response.data;
};

export const createExplainer = async (
  name: string,
  runId: number,
  explainerName: string,
  parameters: object,
): Promise<IExplainer> => {
  const data = {
    name,
    run_id: runId,
    explainer_name: explainerName,
    parameters,
  };

  const response = await api.post<IExplainer>("/v1/explainer/global", data);
  return response.data;
};
