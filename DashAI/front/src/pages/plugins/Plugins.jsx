import React from "react";
import CustomLayout from "../../components/custom/CustomLayout";
import PluginsTab from "./components/PluginsTab";

function PluginsPage() {
  const [refreshPluginsFlag, setRefreshPluginsFlag] = React.useState(true);

  return (
    <CustomLayout>
      <PluginsTab
        refreshPluginsFlag={refreshPluginsFlag}
        setRefreshPluginsFlag={setRefreshPluginsFlag}
      />
    </CustomLayout>
  );
}

export default PluginsPage;
