import { updatePlugin as updatePluginRequest } from "../../../api/plugins";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { PluginStatus } from "../../../types/plugin";

/**
 * custom hook for updating a plugin status
 * @param {string} pluginId
 * @param {enum} newStatus
 * @param {function} onSuccess
 * @returns function to updatePlugin and loading
 */
export default function usePluginsUpdate({ pluginId, newStatus, onSuccess }) {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);

  const updatePlugin = async () => {
    try {
      setLoading(true);
      await updatePluginRequest(pluginId, newStatus);

      onSuccess && onSuccess();
      switch (newStatus) {
        case PluginStatus.INSTALLED:
          enqueueSnackbar("Plugin installed", {
            variant: "success",
          });
          break;
        case PluginStatus.DOWNLOADED:
          enqueueSnackbar("Plugin installed", {
            variant: "success",
          });
          break;
        case PluginStatus.REGISTERED:
          enqueueSnackbar("Plugin uninstalled", {
            variant: "success",
          });
          break;
      }
    } catch (error) {
      enqueueSnackbar("Error while installing plugin.", {
        variant: "error",
      });
    }
    setLoading(false);
  };

  return { updatePlugin, loading };
}
