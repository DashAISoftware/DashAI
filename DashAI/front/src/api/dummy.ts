import api from "./api";

export const getDummy = async (modelName: string): Promise<object> => {
  const response = await api.get<object>("/v1/dummy/");
  return response.data;
};
