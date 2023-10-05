import api from "./api";
import type { ITask } from "../types/task";

export const getTasks = async (): Promise<ITask[]> => {
  const response = await api.get<ITask[]>("/v1/task");
  return response.data;
};
