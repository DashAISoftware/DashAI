import api from "./api";

export const executeRun = async (runId: number): Promise<object> => {
  const formData = new FormData();

  formData.append(
    "params",
    JSON.stringify({
      run_id: runId,
    }),
  );
  const response = await api.post<object>("/v1/runner/", formData);
  return response.data;
};
