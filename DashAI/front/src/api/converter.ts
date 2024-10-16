import api from "./api";
import { IConverter } from "../types/converter";

const converterEndpoint = "/v1/converter";

export const saveDatasetConverterList = async (
  datasetId: number,
  converters: object,
): Promise<IConverter> => {
  const data = {
    dataset_id: datasetId,
    converters: { ...converters },
  };

  const response = await api.post<IConverter>(`${converterEndpoint}`, data);
  return response.data;
};
