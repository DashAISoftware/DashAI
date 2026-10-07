import api from "./api";
import { INotebook, INotebookCreate } from "../types/notebook";
import { IExplorer } from "../types/explorer";
import { IConverter } from "../types/converter";
import { IDocumentContentItem, IDocumentOutlineItem } from "./documents";

const notebookEndpoint = "/v1/notebook/";

export interface INotebookDocumentContentPage {
  notebook_id: number;
  content_type: string;
  total: number;
  offset: number;
  limit: number;
  items: IDocumentContentItem[];
}

export interface INotebookDocumentOutline {
  notebook_id: number;
  total: number;
  items: IDocumentOutlineItem[];
}

export const createNotebook = async (
  data: INotebookCreate,
): Promise<INotebook> => {
  const response = await api.post<INotebook>(notebookEndpoint, data);
  return response.data;
};

export const getNotebookDocumentContent = async (
  notebookId: number | string,
  contentType = "all",
  offset = 0,
  limit = 50,
): Promise<INotebookDocumentContentPage> => {
  const response = await api.get<INotebookDocumentContentPage>(
    `${notebookEndpoint}${notebookId}/document-content`,
    { params: { content_type: contentType, offset, limit } },
  );
  return response.data;
};

export const getNotebookDocumentOutline = async (
  notebookId: number | string,
): Promise<INotebookDocumentOutline> => {
  const response = await api.get<INotebookDocumentOutline>(
    `${notebookEndpoint}${notebookId}/document-outline`,
  );
  return response.data;
};

export const getNotebooks = async (): Promise<INotebook[]> => {
  const response = await api.get<INotebook[]>(notebookEndpoint);
  return response.data;
};

export const getNotebook = async (id: string): Promise<INotebook> => {
  const response = await api.get<INotebook>(`${notebookEndpoint}${id}`);
  return response.data;
};

export const getExplorersByNotebookId = async (
  notebookId: string,
): Promise<IExplorer[]> => {
  const response = await api.get<IExplorer[]>(
    `${notebookEndpoint}${notebookId}/explorers`,
  );
  return response.data;
};

export const getConvertersByNotebookId = async (
  notebookId: string,
): Promise<IConverter[]> => {
  const response = await api.get<IConverter[]>(
    `${notebookEndpoint}${notebookId}/converters`,
  );
  return response.data;
};

export const deleteNotebook = async (id: number): Promise<object> => {
  const response = await api.delete(`${notebookEndpoint}${id}`);
  return response;
};

export const deleteNotebooks = async (ids: number[]): Promise<object> => {
  const response = await api.delete(notebookEndpoint, { data: { ids } });
  return response;
};

export const updateNotebook = async (
  id: number,
  formData: object,
): Promise<INotebook> => {
  const response = await api.patch(`${notebookEndpoint}${id}`, {
    ...formData,
  });
  return response.data;
};
