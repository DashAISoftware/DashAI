import api from "./api";
import { isRepeatedFoldMetrics } from "./run";

import {
  SavedStatisticalTest,
  StatisticalTestResponse,
  StatisticalTestSavePayload,
  StatisticalTestRequest,
} from "../types/statisticalTests";

type FoldMetricsResponse =
  | Record<string, number[]>
  | Record<string, Record<string, number[]>>;

/** Fold scores of a run, flattened over repetitions when CV was repeated. */
export interface RunFoldMetrics {
  /** {metric name: [one score per fold]}, repetitions concatenated in order. */
  metrics: Record<string, number[]>;
  /** Number of CV repetitions (1 when the CV was not repeated). */
  nRepeats: number;
}

/**
 * Flatten a fold-metrics response into one score list per metric.
 *
 * Repeated CV comes back grouped as {rep_0: {metric: [...]}, rep_1: ...}.
 * The repetitions are concatenated in numeric order (rep_10 after rep_9),
 * which restores the original fold order. The statistical tests then treat
 * all r x k scores as independent observations.
 */
export const flattenFoldMetrics = (
  data: FoldMetricsResponse,
): RunFoldMetrics => {
  if (!isRepeatedFoldMetrics(data)) {
    return { metrics: data, nRepeats: 1 };
  }

  const repetitionKeys = Object.keys(data)
    .filter((key) => key.startsWith("rep_"))
    .sort((a, b) => Number(a.slice(4)) - Number(b.slice(4)));

  const metrics: Record<string, number[]> = {};
  for (const key of repetitionKeys) {
    for (const [name, values] of Object.entries(data[key])) {
      metrics[name] = [...(metrics[name] ?? []), ...values];
    }
  }
  return { metrics, nRepeats: repetitionKeys.length };
};

/**
 * Get fold metrics for a specific run and metric split.
 */
export const getFoldMetrics = async (
  runId: string,
  metricSplit: string,
  level: "fold" | "outer" = "fold",
): Promise<RunFoldMetrics> => {
  const response =
    level === "fold"
      ? await api.get<FoldMetricsResponse>(`/v1/run/${runId}/fold-metrics`, {
          params: { metric_split: metricSplit },
        })
      : await api.get<FoldMetricsResponse>(
          `/v1/run/${runId}/outer-fold-metrics`,
          { params: { metric_split: metricSplit } },
        );
  return flattenFoldMetrics(response.data);
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
