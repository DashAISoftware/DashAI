import api from "./api";

export interface IAppConfig {
  tours_autostart: boolean;
}

const appConfigEndpoint = "/v1/app-config";

// Options only change when the backend restarts, so fetch them once per load.
let appConfigPromise: Promise<IAppConfig> | null = null;

export const getAppConfig = (): Promise<IAppConfig> => {
  if (!appConfigPromise) {
    appConfigPromise = api
      .get<IAppConfig>(`${appConfigEndpoint}/`)
      .then((response) => response.data)
      .catch((error) => {
        // Let the next caller retry instead of caching the failure.
        appConfigPromise = null;
        throw error;
      });
  }
  return appConfigPromise;
};

/**
 * Whether guided tours may open by themselves on a first visit. Defaults to
 * true when the backend can't be reached, matching the app's default.
 */
export const getToursAutostart = async (): Promise<boolean> => {
  try {
    const config = await getAppConfig();
    return config.tours_autostart !== false;
  } catch {
    return true;
  }
};
