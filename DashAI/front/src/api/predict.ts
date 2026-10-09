import api from "./api";

import { IParamsFilter } from "../types/predict";
const predictEndpoint = "/v1/predict";

// Returns only the ids of datasets compatible with the run's model - the
// backend checks every dataset's schema in one request, so the frontend can
// filter an already-fetched dataset list by id instead of fetching per-dataset
// info for every candidate up front.
export const filterDatasets = async (
  requestData: IParamsFilter,
): Promise<number[]> => {
  const response = await api.get<{ valid_dataset_ids: number[] }>(
    `${predictEndpoint}/filter_datasets`,
    { params: requestData },
  );
  return response.data.valid_dataset_ids;
};

export const downloadPredict = async (prediction_id: string) => {
  const response = await api.get(
    `${predictEndpoint}/download/${prediction_id}`,
  );
  return response.data;
};

export const createPrediction = async (
  run_id: number,
  dataset_id?: number,
  split?: string | null,
): Promise<object> => {
  const response = await api.post<object>(`${predictEndpoint}/`, {
    run_id,
    dataset_id,
    split,
  });
  return response.data;
};

export interface IPredictionSplit {
  name: string;
  rows: number;
}

/**
 * The partitions the run carved its training dataset into, which a prediction
 * may target when it runs on that same dataset. Which ones exist depends on how
 * the run was evaluated, so the backend decides the list and its names.
 */
export const getPredictionSplits = async (
  runId: number,
): Promise<{
  splits: IPredictionSplit[];
  trainingDatasetId: number | null;
}> => {
  const response = await api.get<{
    splits: IPredictionSplit[];
    training_dataset_id: number | null;
  }>(`${predictEndpoint}/splits/${runId}`);
  return {
    splits: response.data.splits,
    trainingDatasetId: response.data.training_dataset_id,
  };
};

export const getPredictions = async (
  run_id?: number,
  prediction_id?: string,
): Promise<object[]> => {
  const response = await api.get<object[]>(`${predictEndpoint}/`, {
    params: {
      run_id,
      prediction_id,
    },
  });
  return response.data;
};

export const getPredictionSummary = async (
  prediction_id: string,
): Promise<object[]> => {
  const response = await api.get<object[]>(`${predictEndpoint}/summary/`, {
    params: {
      prediction_id,
    },
  });
  return response.data;
};

export const deletePrediction = async (
  prediction_id: string,
): Promise<void> => {
  await api.delete(`${predictEndpoint}/${prediction_id}`);
};

export const previewManualPrediction = async (
  runId: number,
  manualInputData: Record<string, unknown>[],
): Promise<{ columns: string[]; rows: unknown[][] }> => {
  const formData = new FormData();

  const simpleData = manualInputData.map((obj, i) => {
    const cleanObj: Record<string, unknown> = {};
    Object.entries(obj).forEach(([key, value]) => {
      if (value instanceof File) {
        const fileFieldKey = `file_${i}_${key}`;
        formData.append(fileFieldKey, value);
        cleanObj[key] = fileFieldKey;
      } else {
        cleanObj[key] = value;
      }
    });
    return cleanObj;
  });

  formData.append("run_id", String(runId));
  formData.append("manual_input_data", JSON.stringify(simpleData));

  const response = await api.post<{ columns: string[]; rows: unknown[][] }>(
    `${predictEndpoint}/preview`,
    formData,
  );
  return response.data;
};
