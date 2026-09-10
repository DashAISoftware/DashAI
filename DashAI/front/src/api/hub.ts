import api from "./api";

const hubEndpoint = "/v1/dataset-source";

export interface DatasetSourceInfo {
  name: string;
  type: string;
  display_name: string;
  description: string;
}

export interface DatasetEntry {
  id: string;
  name: string;
  description: string;
  tags: string[];
  size_bytes: number | null;
  url: string;
  source: string;
}

export interface DatasetSearchPage {
  results: DatasetEntry[];
  next_cursor: string | null;
}

export interface DatasetPreview {
  sample: Record<string, unknown>[];
  inferred_types: Record<string, unknown>;
  preview_row_count: number;
}

export const searchDatasets = async (
  sourceName: string,
  query: string,
  limit = 20,
  cursor: string | null = null,
  tags: string[] = [],
): Promise<DatasetSearchPage> => {
  const response = await api.get<DatasetSearchPage>(
    `${hubEndpoint}/${sourceName}/search`,
    { params: { q: query, limit, cursor: cursor ?? "", tags } },
  );
  return response.data;
};

export const getDatasetInfo = async (
  sourceName: string,
  datasetId: string,
): Promise<{ id?: string; description?: string; tags?: string[] }> => {
  const encodedId = encodeURIComponent(datasetId);
  const response = await api.get<{
    id?: string;
    description?: string;
    tags?: string[];
  }>(`${hubEndpoint}/${sourceName}/${encodedId}/info`);
  return response.data;
};

export const previewHubDataset = async (
  sourceName: string,
  datasetId: string,
  nRows = 100,
  dataloader?: string,
  params?: Record<string, unknown>,
  hubDownloadId?: number,
  selectedFile?: string,
): Promise<DatasetPreview> => {
  const encodedId = encodeURIComponent(datasetId);
  const response = await api.post<DatasetPreview>(
    `${hubEndpoint}/${sourceName}/${encodedId}/preview`,
    {
      dataloader,
      params: params ?? {},
      n_rows: nRows,
      datafile_id: hubDownloadId ?? null,
      selected_file: selectedFile ?? null,
    },
  );
  return response.data;
};

export const importHubDataset = async (
  sourceName: string,
  datasetId: string,
  dashaiDatasetId: number,
  params: Record<string, unknown>,
): Promise<{ job_id: string; dataset_id: number }> => {
  const encodedId = encodeURIComponent(datasetId);
  const response = await api.post<{ job_id: string; dataset_id: number }>(
    `${hubEndpoint}/${sourceName}/${encodedId}/import`,
    { dataset_id: dashaiDatasetId, params },
  );
  return response.data;
};

// ---- Datafiles ----

const datafileEndpoint = "/v1/datafile";

export type DatafileStatus = "downloading" | "ready" | "error";

export interface Datafile {
  id: number;
  source_name: string;
  dataset_id: string;
  name: string;
  local_path: string | null;
  status: DatafileStatus;
  error_message: string | null;
  size_bytes: number | null;
  description: string;
  tags: string[];
  source_url: string | null;
  created: string | null;
  last_modified: string | null;
  job_id?: string;
}

export const createDatafile = async (
  source_name: string,
  dataset_id: string,
  name: string,
  description: string = "",
  tags: string[] = [],
  source_url: string = "",
): Promise<Datafile> => {
  const response = await api.post<Datafile>(`${datafileEndpoint}/`, {
    source_name,
    dataset_id,
    name,
    description,
    tags,
    source_url,
  });
  return response.data;
};

export const listDatafiles = async (): Promise<Datafile[]> => {
  const response = await api.get<Datafile[]>(`${datafileEndpoint}/`);
  return response.data;
};

export const getDatafile = async (id: number): Promise<Datafile> => {
  const response = await api.get<Datafile>(`${datafileEndpoint}/${id}`);
  return response.data;
};

export const deleteDatafile = async (id: number): Promise<void> => {
  await api.delete(`${datafileEndpoint}/${id}`);
};

export const listDatafileFiles = async (id: number): Promise<string[]> => {
  const response = await api.get<string[]>(`${datafileEndpoint}/${id}/files`);
  return response.data;
};
