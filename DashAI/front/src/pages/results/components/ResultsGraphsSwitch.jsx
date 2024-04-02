import React from "react";
import PropTypes from "prop-types";
import { Switch, Typography, Box } from "@mui/material";

function ResultsGraphsSwitch({ showCustomMetrics, handleToggleMetrics }) {
  return (
    <Box mb={2} display="flex" justifyContent="flex-start" width="100%">
        <Box display="flex" alignItems="center">
        <Typography variant="subtitle2" style={{ fontSize: "0.8rem" }}>General metrics</Typography>
        </Box>
        <Box display="flex" alignItems="center">
        <Switch
            checked={showCustomMetrics}
            onChange={handleToggleMetrics}
            color="primary"
            name="metricsSwitch"
            inputProps={{ 'aria-label': 'Cambiar métricas' }}
        />
        </Box>
        <Box display="flex" alignItems="center">
        <Typography variant="subtitle2" style={{ fontSize: "0.8rem" }}>Custom metrics</Typography>
        </Box>
    </Box>
  );
}

ResultsGraphsSwitch.propTypes = {
    showCustomMetrics: PropTypes.bool.isRequired,
    handleToggleParameter: PropTypes.func,
  };

export default ResultsGraphsSwitch;
