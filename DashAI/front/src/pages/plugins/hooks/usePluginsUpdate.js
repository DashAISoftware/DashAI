import { updatePlugin as updatePluginRequest } from "../../../api/plugins";
import { useSnackbar } from "notistack";
import { PluginStatus } from "../../../types/plugin";

/**
 * custom hook for updating a plugin status
 * @param {string} pluginId
 * @param {enum} newStatus
 * @param {function} onSuccess
 * @returns function to updatePlugin
 */
export default function usePluginsUpdate({ pluginId, newStatus, onSuccess }) {
  const { enqueueSnackbar } = useSnackbar();

  const updatePlugin = async () => {
    try {
      await updatePluginRequest(pluginId, newStatus);

      onSuccess && onSuccess();
      switch (newStatus) {
        case PluginStatus.INSTALLED:
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
  };

  return { updatePlugin };
}
