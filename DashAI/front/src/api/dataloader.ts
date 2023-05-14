import api from "./api";
import type { IDataloader } from "../types/dataloader";

export const getCompatibleDataloaders = async (
  taskName: string,
): Promise<IDataloader[]> => {
  const response = await api.get<IDataloader[]>(`/v1/dataloader/${taskName}`);
  return response.data;
};
