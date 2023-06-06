import api from "./api";
import type { IDataloader } from "../types/dataloader";
import type { ITask } from "../types/task";

interface componentInput {
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
}: componentInput = {}): Promise<Array<ITask | IDataloader | object>> => {
  const queryArray = [];

  // construct the query string of each parameter depending if it was passed in the function call or not
  if (selectTypes.length > 0) {
    const selectTypesQuery = `select_types=${selectTypes.join(
      "&select_types=",
    )}`;
    queryArray.push(selectTypesQuery);
  }

  if (ignoreTypes.length > 0) {
    const ignoreTypesQuery = `ignore_types=${ignoreTypes.join(
      "&ignore_types=",
    )}`;
    queryArray.push(ignoreTypesQuery);
  }

  if (relatedComponent !== "") {
    const relatedComponentQuery = `related_component=${relatedComponent}`;
    queryArray.push(relatedComponentQuery);
  }

  if (componentParent !== "") {
    const componentParentQuery = `component_parent=${componentParent}`;
    queryArray.push(componentParentQuery);
  }

  // join all the queries strings into a single one
  const fullQuery = queryArray.join("&");

  const response = await api.get<Array<ITask | IDataloader | object>>(
    `/v1/component/?${fullQuery}`,
  );
  return response.data;
};
