import usePlugins from "./usePlugins";
import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";

/**
 * custom hook for getting tabs, handle tab change and get plugin tags
 * @param {boolean} refreshPluginsFlag
 * @param {function} setRefreshPluginsFlag
 * @returns tabs to use, tab handlers and plugin tags
 */
export default function usePluginsTab({
  refreshPluginsFlag,
  setRefreshPluginsFlag,
}) {
  const { pluginsBrowse, pluginsInstalled, loading } = usePlugins({
    onSettled: () => {
      setRefreshPluginsFlag(false);
    },
    refresh: refreshPluginsFlag,
  });

  const pluginTags = [
    "DashAI",
    "Package",
    "Task",
    "Model",
    "Dataloaders",
    "Converter",
    "Explainer",
  ];

  const tabs = [
    {
      label: "Browse",
      plugins: pluginsBrowse,
      to: "/app/plugins/browse",
    },
    {
      label: "Installed",
      plugins: pluginsInstalled,
      to: "/app/plugins/installed",
    },
  ];

  const { category } = useParams();

  const currentTab = () => {
    switch (category) {
      case "browse":
        return "0";
      case "installed":
        return "1";
      default:
        return "0";
    }
  };

  const [tabValue, setTabValue] = useState(currentTab());
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    setTabValue(currentTab());
  }, [category]);

  return {
    tabs,
    pluginTags,
    loading,
    tabValue,
    handleTabChange,
  };
}
