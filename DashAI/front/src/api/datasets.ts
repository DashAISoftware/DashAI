import api from "./api";
import type { IDataset } from "../types/dataset";

const datasetEndpoint = "/v1/dataset";

export const copyDataset = async (formData: object): Promise<object> => {
  const response = await api.post<object>(`${datasetEndpoint}/copy`, formData);
  return response.data;
};

export const getDatasets = async (): Promise<IDataset[]> => {
  const response = await api.get<IDataset[]>(`${datasetEndpoint}/`);
  return response.data;
};

export const getDataset = async (id: number): Promise<IDataset> => {
  const response = await api.get<IDataset>(`${datasetEndpoint}/${id}`);
  return response.data;
};

export const getDatasetSample = async (id: number): Promise<object> => {
  const response = await api.get<object>(`${datasetEndpoint}/${id}/sample`);
  return response.data;
};

export const getDatasetSampleByFilePath = async (
  path: string,
): Promise<object> => {
  const response = await api.get<object>(`${datasetEndpoint}/sample/file`, {
    params: { path },
  });
  return response.data;
};

export const getDatasetTypes = async (id: number): Promise<object> => {
  const response = await api.get<object>(`${datasetEndpoint}/${id}/types`);
  return response.data;
};

export const getDatasetTypesByFilePath = async (
  path: string,
): Promise<object> => {
  const response = await api.get<object>(`${datasetEndpoint}/types/file`, {
    params: { path },
  });
  return response.data;
};

export const getDatasetInfo = async (id: number): Promise<object> => {
  const response = await api.get<object>(`${datasetEndpoint}/${id}/info`);
  return response.data;
};

export const getDatasetInfoByFilePath = async (
  path: string,
): Promise<object> => {
  const response = await api.get<object>(`${datasetEndpoint}/file/info`, {
    params: { path },
  });
  return response.data;
};

export const getModelSessionsExist = async (id: number): Promise<object> => {
  const response = await api.get(
    `${datasetEndpoint}/${id}/model-sessions-exist`,
  );
  return response.data;
};

export const createDataset = async (name: string): Promise<IDataset> => {
  const response = await api.post<IDataset>(`${datasetEndpoint}/`, {
    name: name,
  });
  return response.data;
};

export const updateDataset = async (
  id: number,
  formData: object,
): Promise<IDataset> => {
  const response = await api.patch<IDataset>(`${datasetEndpoint}/${id}`, {
    ...formData,
  });
  return response.data;
};

export const renameDatasetColumn = async (
  id: number,
  oldName: string,
  newName: string,
): Promise<{
  message: string;
  old_name: string;
  new_name: string;
  columns: object;
}> => {
  const response = await api.patch(`${datasetEndpoint}/${id}/columns/rename`, {
    old_name: oldName,
    new_name: newName,
  });
  return response.data;
};

export const updateColumnEncoder = async (
  id: number,
  columnName: string,
  encoder: "one_hot" | "label",
): Promise<object> => {
  const response = await api.patch(
    `${datasetEndpoint}/${id}/columns/${columnName}/encoder`,
    { encoder },
  );
  return response.data;
};

export const deleteDataset = async (id: string): Promise<object> => {
  const response = await api.delete(`${datasetEndpoint}/${id}`);
  return response;
};

export const deleteDatasets = async (ids: number[]): Promise<object> => {
  const response = await api.delete(`${datasetEndpoint}/`, {
    data: { ids },
  });
  return response;
};

export const getDatasetFile = async (path: string, page = 0, pageSize = 5) => {
  const response = await api.get(`${datasetEndpoint}/file/`, {
    params: { path, page, page_size: pageSize },
  });
  return response.data;
};

export const exportDatasetCsvById = async (id: number): Promise<Blob> => {
  const response = await api.get(`${datasetEndpoint}/${id}/export/csv`, {
    responseType: "blob",
  });
  return response.data;
};

export const exportDatasetCsvByPath = async (
  path: string,
  filterModel?: object,
  sortModel?: object[],
): Promise<Blob> => {
  const response = await api.get(`${datasetEndpoint}/export/csv`, {
    params: {
      path,
      filter_model: filterModel ? JSON.stringify(filterModel) : undefined,
      sort_model:
        sortModel && sortModel.length > 0
          ? JSON.stringify(sortModel)
          : undefined,
    },
    responseType: "blob",
  });
  return response.data;
};

export const loadPreview = async (formData: FormData): Promise<object> => {
  const response = await api.post(`${datasetEndpoint}/load_preview`, formData);
  return response.data;
};

export const inferDataTypes = async (formData: FormData): Promise<object> => {
  const response = await api.post(
    `${datasetEndpoint}/infer_datatypes`,
    formData,
  );
  return response.data;
};

export const previewWithTypes = async (
  formData: FormData,
): Promise<{
  sample: Array<Record<string, any>>;
  schema: Record<string, { type: string; dtype: string; encoding?: string }>;
  inferred_types: Record<string, { type: string; dtype: string }>;
  preview_row_count: number;
}> => {
  const response = await api.post(
    `${datasetEndpoint}/preview_with_types`,
    formData,
  );
  return response.data;
};

export const validateTypeChanges = async (
  formData: FormData,
): Promise<{
  valid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
}> => {
  const response = await api.post(
    `${datasetEndpoint}/validate_type_changes`,
    formData,
  );
  return response.data;
};

export const getDatasetFileFiltered = async (
  path: string,
  page = 0,
  pageSize = 5,
  filterModel?: object,
  sortModel?: object[],
) => {
  const response = await api.get(`${datasetEndpoint}/filter/`, {
    params: {
      path,
      page,
      page_size: pageSize,
      filterModel: filterModel ? JSON.stringify(filterModel) : undefined,
      sortModel:
        sortModel && sortModel.length > 0
          ? JSON.stringify(sortModel)
          : undefined,
    },
  });
  return response.data;
};
