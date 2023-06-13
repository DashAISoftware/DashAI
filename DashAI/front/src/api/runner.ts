import api from "./api";

export const executeRun = async (runId: number): Promise<object> => {
  const response = await api.post<object>(`/v1/runner?run_id=${runId}`);
  return response.data;
};
