import React from "react";
import CustomLayout from "../../components/custom/CustomLayout";
import PluginsTab from "./components/PluginsTab";
import usePlugins from "./hooks/usePlugins";

function PluginsPage() {
  const {pluginsBrowse, pluginsInstalled, loading} = usePlugins();
  
  return (
    <CustomLayout>
      <PluginsTab pluginsBrowse={pluginsBrowse} pluginsInstalled={pluginsInstalled} loading={loading} ></PluginsTab>
    </CustomLayout>
  );
}

export default PluginsPage;
