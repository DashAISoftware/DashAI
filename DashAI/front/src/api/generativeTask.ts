import api from "./api";
import type { IGenerativeTask } from "../types/generativeTask";
import type { ISession, ISessionParameterHistory } from "../types/session";

export const getGenerativeTask = async (): Promise<IGenerativeTask[]> => {
  const response = await api.get<IGenerativeTask[]>(
    "/v1/component/?select_types=GenerativeTask",
  );
  return response.data;
};

export const getRelatedComponents = async (
  relatedComponent: string,
): Promise<IGenerativeTask[]> => {
  try {
    const response = await api.get<IGenerativeTask[]>(
      `/v1/component/?related_component=${encodeURIComponent(relatedComponent)}`,
    );
    console.log("Related components:", response.data);
    return response.data;
  } catch (error) {
    return [];
  }
};

export const createGenerativeSession = async (
  sessionData: Omit<ISession, "id" | "created" | "last_modified">,
): Promise<ISession> => {
  console.log("Creating new generative session with data:", sessionData);
  const response = await api.post<ISession>(
    "/v1/generative-session/",
    sessionData,
  );
  return response.data;
};

export const updateGenerativeSessionParams = async (
  sessionId: number,
  newParams: Record<string, any>,
): Promise<ISession> => {
  const response = await api.put<ISession>(
    `/v1/generative-session/${sessionId}/parameters`,
    newParams,
  );
  return response.data;
};

export const getGenerativeSession = async (
  sessionId: number,
): Promise<ISession> => {
  const response = await api.get<ISession>(
    `/v1/generative-session/${sessionId}`,
  );
  return response.data;
};

export const getGenerativeSessionParametersHistory = async (
  sessionId: number,
): Promise<ISessionParameterHistory[]> => {
  const response = await api.get<ISessionParameterHistory[]>(
    `/v1/generative-session/${sessionId}/parameters-history`,
  );
  return response.data;
};
