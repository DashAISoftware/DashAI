import api from "./api";
import type { ISession } from "../types/session";

/**
 * Fetches generative sessions, optionally narrowed by the backend.
 * @param filters.taskName - Only sessions of this generative task. A view
 *   scoped to one task uses this; the shared list asks for everything.
 * @returns The matching sessions, oldest first.
 */
export const getSessions = async (filters?: {
  taskName?: string;
}): Promise<ISession[]> => {
  const params: Record<string, string> = {};
  if (filters?.taskName) params.task_name = filters.taskName;
  const response = await api.get<ISession[]>("/v1/generative-session", {
    params,
  });
  return response.data;
};

export const removeSession = async (sessionId: string): Promise<void> => {
  await api.delete(`/v1/generative-session/${sessionId}`);
};

export const removeSessions = async (ids: number[]): Promise<void> => {
  await api.delete("/v1/generative-session/", { data: { ids } });
};

export const getSessionById = async (sessionId: string): Promise<ISession> => {
  const response = await api.get<ISession>(
    `/v1/generative-session/${sessionId}`,
  );
  return response.data;
};

export const getHistoryBySessionId = async (
  sessionId: string,
): Promise<ISession[]> => {
  const response = await api.get<ISession[]>(
    `/v1/generative-session/parameters-history/${sessionId}`,
  );
  return response.data;
};

export const updateGenerativeSession = async ({
  id,
  formData,
}: {
  id: string;
  formData: {
    name?: string;
    task_name?: string;
    description?: string;
    model_name?: string;
  };
}): Promise<object> => {
  const response = await api.patch(`/v1/generative-session/${id}`, null, {
    params: formData,
  });
  return response.data;
};
