import api from "./api";
import type { IRun } from "../types/run";

export const getRuns = async (): Promise<IRun[]> => {
  const response = await api.get<IRun[]>("/v1/run");
  return response.data;
};