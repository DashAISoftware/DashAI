import api from "./api";

export const executeRun = async (runId: number): Promise<object> => {
  const response = await api.post<object>(`/v1/runner?run_id=${runId}`);
  return response.data;
};

export const executeRuns = async (runIds: number[]): Promise<object> => {
  // const responses: object[] = [];

  const sendExecuteRequests = async (
    iterator: IterableIterator<number>,
  ): Promise<void> => {
    for (const item of iterator) {
      await executeRun(item);
      // responses.push(response);
    }
  };
  const iterator = Array.from(runIds).values();
  const nWorkers = 1;
  // starts n workers that share the same iterator
  const workers = Array(nWorkers).fill(iterator).map(sendExecuteRequests);

  const result = await Promise.allSettled(workers);
  return result;
};
