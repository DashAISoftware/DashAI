import api from "./api";
import type { IArtifact } from "../types/artifact";
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
): Promise<IArtifact[]> => {
  const response = await api.get<IArtifact[]>(
    `/v1/explainer/${scope}/plot/${explainerId}`,
  );

  return response.data;
};

export const createGlobalExplainer = async (
  runId: number,
  explainerName: string,
  parameters: object,
): Promise<IExplainer> => {
  const data = {
    run_id: runId,
    explainer_name: explainerName,
    parameters,
  };

  const response = await api.post<IExplainer>("/v1/explainer/global", data);
  return response.data;
};

export const createLocalExplainer = async (
  runId: number,
  explainerName: string,
  datasetId: string,
  parameters: object,
  fitParameters: object,
  scope: object,
): Promise<IExplainer> => {
  const data = {
    run_id: runId,
    dataset_id: datasetId,
    explainer_name: explainerName,
    parameters,
    fit_parameters: fitParameters,
    scope,
  };
  const response = await api.post<IExplainer>("/v1/explainer/local", data);
  return response.data;
};

export const validateDataset = async (
  runId: number,
  datasetId: string,
): Promise<IExplainer> => {
  const data = {
    run_id: runId,
    dataset_id: datasetId,
  };
  const response = await api.post<IExplainer>(
    "/v1/explainer/local/validate-dataset",
    data,
  );
  return response.data;
};

export const getValidDatasets = async (runId: number): Promise<number[]> => {
  const response = await api.post<{ valid_dataset_ids: number[] }>(
    "/v1/explainer/local/valid-datasets",
    { run_id: runId },
  );
  return response.data.valid_dataset_ids;
};

export interface IExplainableSplit {
  name: string;
  rows: number;
}

/**
 * The dataset partitions a run can be explained on. Which ones exist depends on
 * how the run was evaluated, so the backend decides the list and its names.
 */
export const getExplainableSplits = async (
  runId: number,
): Promise<IExplainableSplit[]> => {
  const response = await api.get<{ splits: IExplainableSplit[] }>(
    `/v1/explainer/explainable-splits/${runId}`,
  );
  return response.data.splits;
};

export const deleteExplainer = async (
  scope: string,
  id: string,
): Promise<object> => {
  const response = await api.delete(`/v1/explainer/${scope}/${id}`);
  return response.data;
};

export const saveExplainerPlotOverride = async (
  scope: string,
  explainerId: number,
  index: number,
  figure: unknown,
): Promise<object> => {
  const response = await api.put(
    `/v1/explainer/${scope}/plot/${explainerId}/override`,
    { index, figure },
  );
  return response.data;
};

export const resetExplainerPlotOverride = async (
  scope: string,
  explainerId: number,
  index: number,
): Promise<object> => {
  const response = await api.delete(
    `/v1/explainer/${scope}/plot/${explainerId}/override/${index}`,
  );
  return response.data;
};
