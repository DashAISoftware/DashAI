import api from "./api";

const endpointURL = "/v1/system";

export type InstallChannel =
  "windows" | "macos" | "appimage" | "docker" | "pip" | "source" | "unknown";

export interface UpdateInfo {
  enabled: boolean;
  channel: InstallChannel;
  current_version: string | null;
  latest_version: string | null;
  update_available: boolean;
  release_notes: string | null;
  release_url: string | null;
  download_url: string | null;
  published_at: string | null;
  check_failed: boolean;
}

export const getUpdateCheck = async (): Promise<UpdateInfo> => {
  const response = await api.get<UpdateInfo>(`${endpointURL}/update-check`);
  return response.data;
};

export interface UpdateDownloadStatus {
  available: boolean;
  name: string | null;
  size: number | null;
  downloaded: boolean;
  jobs_running: boolean;
}

export const getUpdateDownloadStatus =
  async (): Promise<UpdateDownloadStatus> => {
    const response = await api.get<UpdateDownloadStatus>(
      `${endpointURL}/update/download`,
    );
    return response.data;
  };

export const startUpdateDownload = async (): Promise<{ id: string }> => {
  const response = await api.post<{ id: string }>(
    `${endpointURL}/update/download`,
  );
  return response.data;
};

export const installUpdate = async (
  stopRunningJobs: boolean,
): Promise<{ channel: InstallChannel }> => {
  const response = await api.post<{ channel: InstallChannel }>(
    `${endpointURL}/update/install`,
    { stop_running_jobs: stopRunningJobs },
  );
  return response.data;
};
