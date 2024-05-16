import api from "./api";
import type { IComponent } from "../types/component";

interface componentQuery {
  model?: string;
  selectTypes?: string[];
  ignoreTypes?: string[];
  relatedComponent?: string;
  componentParent?: string;
}

export const getComponents = async ({
  model = "",
  selectTypes = [],
  ignoreTypes = [],
  relatedComponent = "",
  componentParent = "",
}: componentQuery = {}): Promise<IComponent[]> => {
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

  const response = await api.get<IComponent[]>(`/v1/component/${model}`, {
    params,
    paramsSerializer: {
      indexes: null, // brackets don't appear in the url
    },
  });
  return response.data;
};
