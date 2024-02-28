import { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { getPluginById as getPluginDetailsRequest } from "../../../api/plugins";

/**
 * custom hook to get plugin from the backend using the id
 * @param {string} pluginId
 * @param {boolean} updatePluginFlag
 * @param {function} setUpdatePluginFlag
 * @returns plugin searched by id, loading, error
 */
export default function usePluginsDetails({
  pluginId,
  updatePluginFlag,
  setUpdatePluginFlag,
}) {
  const [loading, setLoading] = useState(true);
  const [plugin, setPlugin] = useState([]);
  const { enqueueSnackbar } = useSnackbar();
  const [error, setError] = useState(false);

  const getPluginsDetails = async () => {
    setLoading(true);
    try {
      const plugin = await getPluginDetailsRequest(pluginId);
      setPlugin(plugin);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain plugin details.", {
        variant: "error",
      });
      setError(true);
    } finally {
      setLoading(false);
      setUpdatePluginFlag(false);
    }
  };

  useEffect(() => {
    if (updatePluginFlag) {
      getPluginsDetails();
    }
  }, [pluginId, updatePluginFlag]);

  return { plugin, loading, error };
}
