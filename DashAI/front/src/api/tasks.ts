import type { ITask } from "../types/task";
import api from "./api";

export const getTasks = async (): Promise<ITask[]> => {
  const response = await api.get<ITask[]>("/v1/task");
  return response.data;
};
