import api from "./api";
import type { IRun } from "../types/run";

export const getRuns = async (modelSessionId: string = ""): Promise<IRun[]> => {
  const params =
    modelSessionId !== "" ? { model_session_id: modelSessionId } : {};
  const response = await api.get<IRun[]>("/v1/run/", { params });
  return response.data;
};

export const getRunById = async (runId: string): Promise<IRun> => {
  const response = await api.get<IRun>(`/v1/run/${runId}`);
  return response.data;
};

export const getHyperparameterPlot = async (
  runId: string,
  plotType: string,
): Promise<IRun> => {
  const response = await api.get<IRun>(`/v1/run/plot/${runId}/${plotType}`);
  return response.data;
};

export const createRun = async (
  modelSessionId: string,
  modelName: string,
  name: string,
  parameters: object,
  optimizerName: string,
  optimizerParameters: object,
  plotHistoryPath: string,
  plotSlicePath: string,
  plotContourPath: string,
  plotImportancePath: string,
  goalMetric: string,
  description: string,
  nested?: object,
): Promise<IRun> => {
  const data = {
    model_session_id: modelSessionId,
    model_name: modelName,
    name,
    parameters,
    optimizer_name: optimizerName,
    optimizer_parameters: optimizerParameters,
    plot_history_path: plotHistoryPath,
    plot_slice_path: plotSlicePath,
    plot_contour_path: plotContourPath,
    plot_importance_path: plotImportancePath,
    goal_metric: goalMetric,
    description,
  };

  if (nested !== undefined) {
    Object.assign(data, { nested });
  }

  const response = await api.post<IRun>("/v1/run/", data);
  return response.data;
};

export const deleteRun = async (runId: string): Promise<void> => {
  await api.delete<void>(`/v1/run/${runId}`);
};

export const updateRunParameters = async (
  runId: string,
  name?: string,
  parameters?: object,
  optimizer?: string,
  optimizer_parameters?: object,
  goal_metric?: string,
  nested?: object,
): Promise<IRun> => {
  const data = {
    run_name: name,
    parameters,
    optimizer,
    optimizer_parameters,
    goal_metric,
  };

  if (nested !== undefined) {
    Object.assign(data, { nested });
  }

  const response = await api.patch<IRun>(`/v1/run/${runId}`, data);
  return response.data;
};

export const resetRunById = async (runId: string): Promise<IRun> => {
  const response = await api.patch<IRun>(`/v1/run/${runId}/reset`);
  return response.data;
};

export const getRunOperationsCount = async (
  runId: string,
): Promise<{ explainers: number; predictions: number }> => {
  const response = await api.get<{ explainers: number; predictions: number }>(
    `/v1/run/${runId}/operations/count`,
  );
  return response.data;
};

export const deleteRunOperations = async (runId: string): Promise<void> => {
  await api.delete<void>(`/v1/run/${runId}/operations`);
};

// ─── Fold Metrics ────────────────────────────────────────────────────────────────

/**
 * Fetch fold-level metrics for a run.
 *
 * Returns either { metric: number[] } (single repetition) or
 * { rep_N: { metric: number[] } } (repeated CV).
 */
export async function getFoldMetrics(
  runId: number,
  {
    metricSplit = "test",
    scope = "default",
    signal,
  }: {
    metricSplit?: "train" | "test";
    scope?: "default" | "outer";
    signal?: AbortSignal;
  } = {},
) {
  const response = await api.get<
    Record<string, number[]> | Record<string, Record<string, number[]>>
  >(`/v1/run/${runId}/fold-metrics`, {
    params: { metric_split: metricSplit, scope },
    signal,
  });
  return response.data;
}

/** True when the response is grouped by repetition ("rep_*"). */
export function isRepeatedFoldMetrics(
  data: Record<string, number[]> | Record<string, Record<string, number[]>>,
): data is Record<string, Record<string, number[]>> {
  return Object.keys(data).some((key) => key.startsWith("rep_"));
}

export async function getOuterAveragedMetrics(
  runId: string,
  { signal }: { signal?: AbortSignal } = {},
) {
  const response = await api.get(`/v1/run/${runId}/outer-averaged-metrics`, {
    signal,
  });
  return response.data;
}
