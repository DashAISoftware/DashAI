import React, { useEffect } from "react";
import { Box, Tab, Tabs, Typography } from "@mui/material";
import { TabContext, TabPanel } from "@mui/lab";
import PropTypes from "prop-types";
import PluginsContent from "./PluginsContent";
import { Link, useParams } from "react-router-dom";

function PluginsTab({ pluginsBrowse, pluginsInstalled, loading }) {
  const { category, id } = useParams();
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

  const currentTab = () => {
    if (id !== undefined) {
      return "0";
    } else {
      switch (category) {
        case "browse":
          return "0";
        case "installed":
          return "1";
        default:
          return "0";
      }
    }
  };

  const [value, setValue] = React.useState(currentTab());
  const handleTabChange = (event, newValue) => {
    setValue(newValue);
  };

  useEffect(() => {
    setValue(currentTab());
  }, [category, id]);

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs value={value} onChange={handleTabChange} aria-label="tabs">
            {tabs.map(({ label, to }, i) => (
              <Tab
                component={Link}
                key={i}
                label={label}
                value={i.toString()}
                to={to}
              />
            ))}
          </Tabs>
        </Box>
        {tabs.map(({ label, plugins }, i) => (
          <TabPanel key={i} value={i.toString()} sx={{ p: 0 }}>
            <Typography variant="h4" py={2}>
              {label} Plugins
            </Typography>
            {!loading && <PluginsContent Plugins={plugins} />}
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
}

PluginsTab.propTypes = {
  pluginsBrowse: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      tags: PropTypes.arrayOf(PropTypes.string).isRequired,
      installed: PropTypes.bool,
    }),
  ),
  pluginsInstalled: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      tags: PropTypes.arrayOf(PropTypes.string).isRequired,
      installed: PropTypes.bool,
    }),
  ),
  loading: PropTypes.bool,
};

export default PluginsTab;
