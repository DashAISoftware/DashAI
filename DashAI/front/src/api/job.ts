import api from "./api";

export const getJobs = async (): Promise<object> => {
  const response = await api.get<object>("/v1/job/");
  return response.data;
};

export const enqueueRunnerJob = async (runId: number): Promise<object> => {
  const data = {
    run_id: runId,
  };

  const response = await api.post<object>("/v1/job/runner/", data);
  return response.data;
};

export const startJobQueue = async (
  stopWhenQueueEmpties: boolean | undefined,
): Promise<object> => {
  let params = {};

  if (stopWhenQueueEmpties !== undefined) {
    params = { ...params, stop_when_queue_empties: stopWhenQueueEmpties };
  }

  const response = await api.post<object>("/v1/job/start/", null, { params });
  return response.data;
};
