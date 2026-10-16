import api from "./api";
import type {
  IColumnRef,
  IConverterStep,
  IExportPreview,
  IModelSession,
  ISessionImportResult,
  IStructureResult,
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
  inputColumns: string[],
  outputColumns: string[],
  trainMetrics: string[],
  validationMetrics: string[],
  testMetrics: string[],
  evaluationStrategy: string,
  splitsValue: JSON,
  preprocessing: IConverterStep[] = [],
  inputColumnRefs: IColumnRef[] = [],
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
    preprocessing: preprocessing,
    input_column_refs: inputColumnRefs,
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
  inputRefs?: IColumnRef[],
  // With preprocessing, the backend types every input ref from the chain's
  // estimated structure.
  preprocessing?: IConverterStep[],
): Promise<object> => {
  const formData = {
    task_name: taskName,
    dataset_id: datasetId,
    inputs_columns: inputColumns,
    outputs_columns: outputColumns,
    input_refs: inputRefs,
    preprocessing: preprocessing?.map(({ converter, params, scope }) => ({
      converter,
      params,
      scope,
    })),
  };
  const response = await api.post<object>(
    "/v1/model-session/validation",
    formData,
  );
  return response.data;
};

// Estimate the dataset state after every step of a preprocessing chain,
// without fitting anything (see the backend's infer_structure).
export const getPreprocessingStructure = async ({
  datasetId,
  candidates,
  outputColumns,
  steps,
}: {
  datasetId: number;
  candidates: string[];
  outputColumns: string[];
  steps: IConverterStep[];
}): Promise<IStructureResult> => {
  const response = await api.post<IStructureResult>(
    `${endpointURL}/preprocessing/structure`,
    {
      dataset_id: datasetId,
      candidates,
      output_columns: outputColumns,
      steps: steps.map(({ converter, params, scope }) => ({
        converter,
        params,
        scope,
      })),
    },
  );
  return response.data;
};

export const getSessionExportPreview = async (
  id: number,
): Promise<IExportPreview> => {
  const response = await api.get<IExportPreview>(
    `${endpointURL}/${id}/export/preview`,
  );
  return response.data;
};

export const exportModelSession = async (
  id: number,
  runIds: number[],
  includeTrainedModels: boolean,
): Promise<Blob> => {
  const response = await api.post(
    `${endpointURL}/${id}/export`,
    { run_ids: runIds, include_trained_models: includeTrainedModels },
    { responseType: "blob" },
  );
  return response.data;
};

export const importModelSession = async (
  file: File,
): Promise<ISessionImportResult> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<ISessionImportResult>(
    `${endpointURL}/import`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
};
