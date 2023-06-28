import React, { useState } from "react";
import PropTypes from "prop-types";
import {
  Divider,
  Grid,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

/**
 * Component that displays the metrics associated with a run.
 * @param {object} runData object that contains all the necesary info of the
 */
function RunMetricsTab({ runData }) {
  const [displaySet, setDisplaySet] = useState("test_metrics");

  const getDisplaySetName = () => {
    switch (displaySet) {
      case "test_metrics":
        return "test";
      case "train_metrics":
        return "train";
      case "validation_metrics":
        return "validation";
      default:
        throw new Error(`Error, set name ${displaySet} is not recognized`);
    }
  };

  return (
    <Grid container direction="column" rowSpacing={2}>
      {/* Toggle to select the set on which the metrics are applied.  */}
      <Grid item>
        <ToggleButtonGroup
          value={displaySet}
          exclusive
          onChange={(event, newSet) => {
            // condition to enforce value set
            if (newSet !== null) {
              setDisplaySet(newSet);
            }
          }}
          sx={{ float: "right" }}
        >
          <ToggleButton value="test_metrics">Test</ToggleButton>
          <ToggleButton value="train_metrics">Train</ToggleButton>
          <ToggleButton value="validation_metrics">Validation</ToggleButton>
        </ToggleButtonGroup>
      </Grid>

      {/* metrics */}
      <Grid item>
        <Paper variant="outlined" sx={{ borderRadius: 4 }}>
          <Grid container direction="column" rowSpacing={2} sx={{ mt: 1 }}>
            {Object.keys(runData[displaySet]).length === 0 && (
              <Typography variant="p" sx={{ p: 3 }}>
                {`There are no metrics associated to the ${getDisplaySetName()} set in this run`}
              </Typography>
            )}
            {Object.keys(runData[displaySet]).map((metric) => (
              <Grid item key={metric} sx={{ px: 5, py: 1, width: "100%" }}>
                <Typography variant="p">{metric}</Typography>
                <Typography variant="p" sx={{ float: "right" }}>
                  {runData[displaySet][metric].toFixed(2)}
                </Typography>
                <Divider sx={{ mt: 1 }} />
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

RunMetricsTab.propTypes = {
  runData: PropTypes.shape({
    train_metrics: PropTypes.object,
    test_metrics: PropTypes.object,
    validation_metrics: PropTypes.object,
  }),
};

export default RunMetricsTab;
