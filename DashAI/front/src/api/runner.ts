import api from "./api";

export const executeRun = async (runId: number): Promise<object> => {
  const data = {
    run_id: runId,
  };

  const response = await api.post<object>("/v1/runner/", data);
  return response.data;
};
