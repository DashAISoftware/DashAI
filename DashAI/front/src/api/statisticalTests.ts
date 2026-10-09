import api from "./api";

import {
  SavedStatisticalTest,
  StatisticalTestResponse,
  StatisticalTestSavePayload,
  StatisticalTestRequest,
} from "../types/statisticalTests";

/**
 * Get fold metrics for a specific run and metric split.
 */
export const getFoldMetrics = async (
  runId: string,
  metricSplit: string,
  level: "fold" | "outer" = "fold",
): Promise<Record<string, number[]>> => {
  const response =
    level === "fold"
      ? await api.get<Record<string, number[]>>(
          `/v1/run/${runId}/fold-metrics`,
          { params: { metric_split: metricSplit } },
        )
      : await api.get<Record<string, number[]>>(
          `/v1/run/${runId}/outer-fold-metrics`,
          { params: { metric_split: metricSplit } },
        );
  return response.data;
};

/**
 * Run a statistical test on selected runs.
 * Automatically includes post-hoc results when applicable
 * (Nemenyi after significant Friedman, Tukey after significant ANOVA).
 */
export const runStatisticalTest = async (
  request: StatisticalTestRequest,
): Promise<StatisticalTestResponse> => {
  const response = await api.post<StatisticalTestResponse>(
    "/v1/statistical-tests/run",
    request,
  );
  return response.data;
};

/**
 * Save one or more statistical test results to the database.
 * Send a single-element array for an omnibus result, or N elements for a
 * per-run batch (e.g. Shapiro); the backend groups a batch under one group_id.
 */
export const saveStatisticalTestResults = async (
  results: StatisticalTestSavePayload[],
): Promise<SavedStatisticalTest[]> => {
  const response = await api.post<SavedStatisticalTest[]>(
    "/v1/statistical-tests/save",
    results,
  );
  return response.data;
};

/**
 * List saved statistical test results, optionally filtered by model session or
 * batch group.
 */
export const getSavedStatisticalTests = async (
  modelSessionId?: number,
  groupId?: string,
): Promise<SavedStatisticalTest[]> => {
  const response = await api.get<SavedStatisticalTest[]>(
    "/v1/statistical-tests/saved",
    {
      params: {
        ...(modelSessionId != null ? { model_session_id: modelSessionId } : {}),
        ...(groupId != null ? { group_id: groupId } : {}),
      },
    },
  );
  return response.data;
};

/**
 * Delete a saved statistical test result by id.
 */
export const deleteSavedStatisticalTest = async (
  resultId: number,
): Promise<{ deleted: boolean; id: number }> => {
  const response = await api.delete<{ deleted: boolean; id: number }>(
    `/v1/statistical-tests/saved/${resultId}`,
  );
  return response.data;
};
