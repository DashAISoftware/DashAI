import api from "./api";
import type { ICredential } from "../types/credential";

export const getCredentials = async (): Promise<ICredential[]> => {
  const response = await api.get<ICredential[]>("/v1/credential/");
  return response.data;
};

export const authenticateCredential = async (
  name: string,
  key: string,
): Promise<{ is_authenticated: boolean }> => {
  const response = await api.post<{ is_authenticated: boolean }>(
    `/v1/credential/${name}/auth`,
    { key },
  );
  return response.data;
};

export const deleteCredential = async (
  name: string,
): Promise<{ is_authenticated: boolean }> => {
  const response = await api.delete<{ is_authenticated: boolean }>(
    `/v1/credential/${name}`,
  );
  return response.data;
};
