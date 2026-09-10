import api from "./api";
import type { IModelSession } from "../types/modelSession";

const endpointURL = "/v1/model-session";

export const getModelSessions = async (): Promise<IModelSession[]> => {
  const response = await api.get<IModelSession[]>(`${endpointURL}/`);
  return response.data;
};

export const getModelSessionById = async (
  id: string,
): Promise<IModelSession> => {
  const response = await api.get<IModelSession>(`${endpointURL}/${id}`);
  return response.data;
};

export const createModelSession = async (
  datasetId: number,
  taskName: string,
  name: string,
  inputColumns: string[],
  outputColumns: string[],
  trainMetrics: string[],
  validationMetrics: string[],
  testMetrics: string[],
  evaluationStrategy: string,
  splitsValue: JSON,
): Promise<IModelSession> => {
  const data = {
    dataset_id: datasetId,
    task_name: taskName,
    name: name,
    input_columns: inputColumns,
    output_columns: outputColumns,
    train_metrics: trainMetrics,
    validation_metrics: validationMetrics,
    test_metrics: testMetrics,
    evaluation_strategy: evaluationStrategy,
    splits: splitsValue,
  };

  const response = await api.post<IModelSession>("/v1/model-session/", data);
  return response.data;
};

// ver lo de actualizar tambien el evaluation strategy
export const updateModelSession = async ({
  id,
  formData,
}: {
  id: string;
  formData: { name?: string; dataset_id?: number; task_name?: string };
}): Promise<object> => {
  const response = await api.patch(`/v1/model-session/${id}`, null, {
    params: formData,
  });
  return response.data;
};

export const deleteModelSession = async (id: string): Promise<object> => {
  const response = await api.delete(`/v1/model-session/${id}`);
  return response.data;
};

export const deleteModelSessions = async (ids: number[]): Promise<object> => {
  const response = await api.delete("/v1/model-session/", {
    data: { ids },
  });
  return response.data;
};

export const validateColumns = async (
  taskName: string,
  datasetId: number,
  inputColumns: string[],
  outputColumns: string[],
): Promise<object> => {
  const formData = {
    task_name: taskName,
    dataset_id: datasetId,
    inputs_columns: inputColumns,
    outputs_columns: outputColumns,
  };
  const response = await api.post<object>(
    "/v1/model-session/validation",
    formData,
  );
  return response.data;
};
