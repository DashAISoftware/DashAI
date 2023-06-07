import api from "./api";
import type { IDataloader } from "../types/dataloader";
import type { ITask } from "../types/task";

interface componentQuery {
  selectTypes?: string[];
  ignoreTypes?: string[];
  relatedComponent?: string;
  componentParent?: string;
}

export const getComponents = async ({
  selectTypes = [],
  ignoreTypes = [],
  relatedComponent = "",
  componentParent = "",
}: componentQuery = {}): Promise<Array<ITask | IDataloader | object>> => {
  let params = {};

  if (selectTypes.length > 0) {
    params = { ...params, select_types: selectTypes };
  }

  if (ignoreTypes.length > 0) {
    params = { ...params, ignore_types: ignoreTypes };
  }

  if (relatedComponent !== "") {
    params = { ...params, related_component: relatedComponent };
  }

  if (componentParent !== "") {
    params = { ...params, component_parent: componentParent };
  }

  const response = await api.get<Array<ITask | IDataloader | object>>(
    `/v1/component/`,
    {
      params,
      paramsSerializer: {
        indexes: null, // brackets don't appear in the url
      },
    },
  );
  return response.data;
};
