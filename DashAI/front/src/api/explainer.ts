import api from "./api";
import type { IExplainer } from "../types/explainer";

export const getExplainers = async (
  runId: string = "",
): Promise<IExplainer[]> => {
  const params = runId !== "" ? { run_id: runId } : {};
  const response = await api.get<IExplainer[]>("/v1/explainer/", { params });
  return response.data;
};
