import api from "./api";
import type { IFolder } from "../types/folder";

export type { IFolder };

const folderEndpoint = "/v1/folder";

export const getFolders = async (): Promise<IFolder[]> => {
  const response = await api.get<IFolder[]>(`${folderEndpoint}/`);
  return response.data;
};

export const createFolder = async (name: string): Promise<IFolder> => {
  const response = await api.post<IFolder>(`${folderEndpoint}/`, { name });
  return response.data;
};

export const updateFolder = async (
  id: number,
  name: string,
): Promise<IFolder> => {
  const response = await api.patch<IFolder>(`${folderEndpoint}/${id}`, {
    name,
  });
  return response.data;
};

export const deleteFolder = async (id: number): Promise<void> => {
  await api.delete(`${folderEndpoint}/${id}`);
};
