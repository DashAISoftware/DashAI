import { useEffect, useState } from "react";
import { getPlugins as getPluginsRequest } from "../../../api/plugins";

export default function usePlugins() {
  const [loading, setLoading] = useState(true);
  const [pluginsBrowse, setPluginsBrowse] = useState([]);
  const [pluginsInstalled, setPluginsInstalled] = useState([]);

  const getPlugins = async () => {
    setLoading(true);
    try {
      const plugins = await getPluginsRequest();
      setPluginsBrowse(plugins.filter((plugin) => !plugin.installed));
      setPluginsInstalled(plugins.filter((plugin) => plugin.installed));
    } catch (error) {
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getPlugins();
  }, []);

  return { pluginsBrowse, pluginsInstalled, loading };
}
