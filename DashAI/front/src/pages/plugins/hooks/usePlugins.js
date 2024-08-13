import { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { getPlugins as getPluginsRequest } from "../../../api/plugins";
import { PluginStatus } from "../../../types/plugin";

/**
 * Custom hook to get plugins from the backend
 * @param {function} onSettled
 * @param {boolean} refresh
 * @returns pluginsBrowse, pluginsInstalled, loading
 */
export default function usePlugins({ onSettled, refresh = false }) {
  const [loading, setLoading] = useState(true);
  const [pluginsBrowse, setPluginsBrowse] = useState([]);
  const [pluginsInstalled, setPluginsInstalled] = useState([]);
  const { enqueueSnackbar } = useSnackbar();

  const getPlugins = async () => {
    setLoading(true);
    try {
      const plugins = await getPluginsRequest();
      setPluginsBrowse(
        plugins.filter((plugin) =>
          [PluginStatus.REGISTERED].includes(plugin.status),
        ),
      );
      setPluginsInstalled(
        plugins.filter((plugin) =>
          [PluginStatus.INSTALLED].includes(plugin.status),
        ),
      );
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain plugins.", {
        variant: "error",
      });
    } finally {
      onSettled && onSettled();
      setLoading(false);
    }
  };

  useEffect(() => {
    if (refresh) {
      getPlugins();
    }
  }, [refresh]);

  return { pluginsBrowse, pluginsInstalled, loading };
}
