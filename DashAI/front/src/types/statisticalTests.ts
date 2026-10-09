export interface PairwiseResult {
  run_1: number;
  run_1_name?: string;
  run_2: number;
  run_2_name?: string;
  p_value: number;
  significant: boolean;
}

/**
 * Request payload for running a statistical test.
 */
export interface StatisticalTestRequest {
  test_name: string;
  metric_name: string;
  metric_split: string;
  run_ids: number[];
  run_names: Record<string, string>;
  fold_metrics: Record<string, number[]>;
  alpha?: number;
  params?: Record<string, unknown>;
}

export interface StatisticalTestResponse {
  test_name: string;
  statistic: number | null;
  p_value: number | null;
  significant: boolean;
  alpha: number;
  details: Record<string, unknown> | null;
  interpretation?: string | null;
  posthoc: PairwiseResult[] | null;
}

/**
 * Payload sent to persist a single statistical test result.
 */
export interface StatisticalTestSavePayload {
  test_name: string;
  metric_name: string;
  metric_split: string;
  alpha: number;
  significant: boolean;
  run_ids?: number[];
  run_names?: Record<string, string>;
  statistic?: number | null;
  p_value?: number | null;
  interpretation?: string | null;
  params?: Record<string, unknown> | null;
  details?: Record<string, unknown> | null;
  posthoc?: Record<string, unknown>[] | null;
  group_id?: string | null;
  model_session_id?: number | null;
  name?: string | null;
  description?: string | null;
}

/** A stored statistical test result returned by the backend. */
export interface SavedStatisticalTest extends StatisticalTestSavePayload {
  id: number;
  created_at: string;
}
