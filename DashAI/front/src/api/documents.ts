import api from "./api";

const documentsEndpoint = "/v1/documents";
const documentsUrlBase = "/api/v1/documents";

export interface IDataDocument {
  id: number;
  name: string;
  file_name: string | null;
  file_type: string | null;
  file_path: string | null;
  dataloader: string | null;
  dataloader_params: Record<string, unknown> | null;
  content_counts: Record<string, number> | null;
  total_pages: number | null;
  folder_id: number | null;
  status: number;
  created: string;
  last_modified: string;
}

export interface IDocumentContentItem {
  type: "Text" | "Image";
  position: number;
  page: number | null;
  kind: string;
  attrs: Record<string, unknown>;
  content?: string;
  url?: string;
}

export interface IDocumentContentPage {
  document_id: number;
  content_type: string;
  total: number;
  offset: number;
  limit: number;
  items: IDocumentContentItem[];
}

export interface IDocumentCreateParams {
  name: string;
  file_name: string;
  dataloader: string;
  dataloader_params: Record<string, unknown>;
}

export const createDocumentFromNotebook = async (
  name: string,
  notebookId: number,
): Promise<IDataDocument> => {
  const response = await api.post<IDataDocument>(
    `${documentsEndpoint}/from-notebook`,
    { name, notebook_id: notebookId },
  );
  return response.data;
};

export const getDocuments = async (): Promise<IDataDocument[]> => {
  const response = await api.get<IDataDocument[]>(`${documentsEndpoint}/`);
  return response.data;
};

export const getDocument = async (id: number): Promise<IDataDocument> => {
  const response = await api.get<IDataDocument>(`${documentsEndpoint}/${id}`);
  return response.data;
};

export const createDocument = async (
  params: IDocumentCreateParams,
): Promise<IDataDocument> => {
  const response = await api.post<IDataDocument>(
    `${documentsEndpoint}/`,
    params,
  );
  return response.data;
};

export const updateDocument = async (
  id: number,
  data: { name?: string; folder_id?: number | null },
): Promise<IDataDocument> => {
  const response = await api.patch<IDataDocument>(
    `${documentsEndpoint}/${id}`,
    data,
  );
  return response.data;
};

export const deleteDocument = async (id: number): Promise<void> => {
  await api.delete(`${documentsEndpoint}/${id}`);
};

export const getDocumentContent = async (
  id: number,
  contentType = "all",
  offset = 0,
  limit = 50,
): Promise<IDocumentContentPage> => {
  const response = await api.get<IDocumentContentPage>(
    `${documentsEndpoint}/${id}/content`,
    { params: { content_type: contentType, offset, limit } },
  );
  return response.data;
};

export interface IDocumentOutlineItem {
  position: number;
  type: "Text" | "Image";
  kind: string;
  page: number | null;
  level: number | null;
  label: string | null;
}

export interface IDocumentOutline {
  document_id: number;
  total: number;
  items: IDocumentOutlineItem[];
}

export const getDocumentOutline = async (
  id: number,
): Promise<IDocumentOutline> => {
  const response = await api.get<IDocumentOutline>(
    `${documentsEndpoint}/${id}/outline`,
  );
  return response.data;
};

export const getDocumentSourceViewUrl = (
  id: number,
  version?: string | null,
): string =>
  version
    ? `${documentsUrlBase}/${id}/source/view?v=${encodeURIComponent(version)}`
    : `${documentsUrlBase}/${id}/source/view`;

export const getDocumentSourceDownloadUrl = (id: number): string =>
  `${documentsUrlBase}/${id}/source`;

export const enqueueDocumentJob = async (
  documentId: number,
  name: string,
  file: File,
): Promise<{ id: string }> => {
  const formData = new FormData();
  formData.append("job_type", "DocumentJob");
  formData.append("kwargs", JSON.stringify({ document_id: documentId, name }));
  formData.append("file", file);
  const response = await api.post<{ id: string }>("/v1/job/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
      filename: encodeURIComponent(file.name),
    },
  });
  return response.data;
};
