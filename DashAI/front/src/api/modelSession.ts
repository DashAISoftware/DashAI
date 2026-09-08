import api from "./api";
import type {
  IModelSession,
  IOutputSlot,
  ISessionConverter,
  SessionColumn,
} from "../types/modelSession";

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
  inputColumns: SessionColumn[],
  outputColumns: SessionColumn[],
  trainMetrics: string[],
  validationMetrics: string[],
  testMetrics: string[],
  evaluationStrategy: string,
  splitsValue: JSON,
  converters: ISessionConverter[] = [],
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
    converters: converters,
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
  formData: {
    name?: string;
    dataset_id?: number;
    task_name?: string;
    input_columns?: SessionColumn[];
    output_columns?: SessionColumn[];
    splits?: string;
    evaluation_strategy?: string;
  };
}): Promise<IModelSession> => {
  const params: Record<string, unknown> = { ...formData };
  if (formData.input_columns !== undefined) {
    params.input_columns = JSON.stringify(formData.input_columns);
  }
  if (formData.output_columns !== undefined) {
    params.output_columns = JSON.stringify(formData.output_columns);
  }
  const response = await api.patch(`${endpointURL}/${id}`, null, { params });
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
  modelSessionId?: number,
): Promise<object> => {
  const formData = {
    task_name: taskName,
    dataset_id: datasetId,
    inputs_columns: inputColumns,
    outputs_columns: outputColumns,
    ...(modelSessionId !== undefined
      ? { model_session_id: modelSessionId }
      : {}),
  };
  const response = await api.post<object>(
    "/v1/model-session/validation",
    formData,
  );
  return response.data;
};

export const updateSessionConverters = async (
  id: string,
  converters: ISessionConverter[],
): Promise<IModelSession> => {
  const response = await api.put<IModelSession>(
    `${endpointURL}/${id}/converters`,
    { converters },
  );
  return response.data;
};

/**
 * Real output slots for a list of already-configured converters, each
 * instantiated with its own actual `params` — unlike the generic
 * `/component/{name}/` metadata (which always reflects a converter's
 * *default* params), this reflects what the specific converter instance
 * in `converters` really declares (e.g. a `SimpleImputer` configured with
 * `add_indicator: true` shows its second `missing_indicator` slot).
 * Keyed by each entry's own `id`.
 */
export const getConvertersOutputSlots = async (
  converters: ISessionConverter[],
): Promise<Record<string, IOutputSlot[]>> => {
  const response = await api.post<Record<string, IOutputSlot[]>>(
    `${endpointURL}/converters/output-slots`,
    { converters },
  );
  return response.data;
};
