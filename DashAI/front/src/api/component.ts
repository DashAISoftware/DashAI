import api from "./api";
import type { IComponent } from "../types/component";

interface componentQuery {
  model?: string;
  selectTypes?: string[];
  ignoreTypes?: string[];
  relatedComponent?: string;
  componentParent?: string;
  hasRelatedOfType?: string;
}

export const getComponents = async ({
  model = "",
  selectTypes = [],
  ignoreTypes = [],
  relatedComponent = "",
  hasRelatedOfType = "",
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

  if (hasRelatedOfType !== "") {
    params = { ...params, has_related_of_type: hasRelatedOfType };
  }

  const url = model ? `/v1/component/${model}/` : `/v1/component/`;
  const response = await api.get<IComponent[]>(url, {
    params,
    paramsSerializer: {
      indexes: null, // brackets don't appear in the url
    },
  });
  return response.data;
};

export const getChildComponents = async (
  componentName: string,
  recursive: boolean,
): Promise<IComponent[]> => {
  const response = await api.get<IComponent[]>(
    `/v1/component/${componentName}/children`,
    {
      params: { recursive },
    },
  );
  return response.data;
};
export const getComponentById = async (id: string): Promise<IComponent> => {
  const response = await api.get<IComponent>(`/v1/component/${id}/`);
  return response.data;
};

export const downloadComponent = async (
  name: string,
): Promise<{ id: string }> => {
  const response = await api.post<{ id: string }>(
    `/v1/component/${name}/download`,
  );
  return response.data;
};

export const deleteComponentDownload = async (name: string): Promise<void> => {
  await api.delete(`/v1/component/${name}/download`);
};

export const getComponentDownloadStatus = async (
  name: string,
): Promise<{ downloaded: boolean; requires_download: boolean }> => {
  const response = await api.get<{
    downloaded: boolean;
    requires_download: boolean;
  }>(`/v1/component/${name}/download`);
  return response.data;
};

export interface RequiredDownload {
  name: string;
  display_name: string;
  parent: string | null;
  download_size_bytes: number | null;
}

// Resolve which components a configuration still needs downloaded. Walks
// nested component parameters server-side (a component selected as another
// component's parameter) and optionally checks the parent model itself.
export const getRequiredDownloads = async (
  parameters: Record<string, unknown>,
  modelName?: string,
): Promise<RequiredDownload[]> => {
  const response = await api.post<RequiredDownload[]>(
    `/v1/component/downloads/required`,
    { model_name: modelName ?? null, parameters },
  );
  return response.data;
};
