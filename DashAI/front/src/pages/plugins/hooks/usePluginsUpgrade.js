import { upgradePlugin as upgradePluginRequest } from "../../../api/plugins";
import { useSnackbar } from "notistack";

/**
 * custom hook for upgrading a plugin
 * @param {string} pluginId
 * @returns function to upgrade a plugin
 */
export default function usePluginsUpgrade({ pluginId }) {
  const { enqueueSnackbar } = useSnackbar();

  const upgradePlugin = async () => {
    try {
      await upgradePluginRequest(pluginId);
      enqueueSnackbar("Plugin upgraded", {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar("Error while upgrading plugin", {
        variant: "error",
      });
    }
  };

  return { upgradePlugin };
}
