import api from "./api";
import { INotebook } from "../types/notebook";
import { IExplorer } from "../types/explorer";
import { IConverter } from "../types/converter";

const notebookEndpoint = "/v1/notebook/";

export const createNotebook = async (data: INotebook) => {
  const response = await api.post(notebookEndpoint, data);
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
