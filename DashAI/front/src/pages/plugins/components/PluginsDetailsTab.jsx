import React from "react";
import { Box, Tab, Tabs } from "@mui/material";
import { TabContext, TabPanel } from "@mui/lab";
import PropTypes from "prop-types";

/**
 * component to display plugin details tabs
 * @param {} tabs
 * @returns
 */
function PluginsDetailsTab({ tabs }) {
  const [value, setValue] = React.useState("0");
  const handleTabChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ width: "100%" }}>
      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs value={value} onChange={handleTabChange} aria-label="tabs">
            {tabs.map(({ label, to }, i) => (
              <Tab key={i} label={label} value={i.toString()} />
            ))}
          </Tabs>
        </Box>
        {tabs.map(({ label, component }, i) => (
          <TabPanel key={i} value={i.toString()} sx={{ p: 0 }}>
            {component}
          </TabPanel>
        ))}
      </TabContext>
    </Box>
  );
}

PluginsDetailsTab.propTypes = {
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      component: PropTypes.object.isRequired,
    }),
  ).isRequired,
};

export default PluginsDetailsTab;
