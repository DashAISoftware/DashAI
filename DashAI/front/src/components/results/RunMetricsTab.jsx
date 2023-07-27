import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  AlertTitle,
  Box,
  Divider,
  Grid,
  LinearProgress,
  Link,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

/**
 * Component that displays the metrics associated with a run.
 * @param {object} runData object that contains all the necesary info of the
 */
function RunMetricsTab({ runData, setUpdateDataFlag }) {
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

  // on mount, polling to update the sate of the data
  useEffect(() => {
    const intervalId = setInterval(() => {
      // Check the condition to update the state or stop the interval
      if (runData.status === 3 && runData[displaySet] === null) {
        setUpdateDataFlag(true);
      } else {
        // Stop the interval when the condition is no longer met
        clearInterval(intervalId);
      }
    }, 1000);

    // Cleanup the interval when the component is unmounted or the dependency array changes
    return () => clearInterval(intervalId);
  }, [runData.status, runData[displaySet]]);

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
        <Paper sx={{ borderRadius: 4 }}>
          <Grid container direction="column" rowSpacing={2} sx={{ mt: 1 }}>
            {runData[displaySet] === null ? (
              runData.status === 3 ? (
                <Box sx={{ width: "100%" }}>
                  <LinearProgress />
                </Box>
              ) : (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <AlertTitle>
                    {`There are no metrics associated with the ${getDisplaySetName()} set in this run`}
                  </AlertTitle>
                  Go to{" "}
                  <Link component={RouterLink} to="/app/experiments">
                    experiments tab
                  </Link>{" "}
                  to run your experiment.
                </Alert>
              )
            ) : Object.keys(runData[displaySet]).length === 0 ? (
              <Alert severity="error" sx={{ mb: 2 }}>
                <AlertTitle>Error</AlertTitle>
                <Typography variant="body1">
                  The result metrics for {getDisplaySetName()} set are empty.
                </Typography>
              </Alert>
            ) : (
              Object.keys(runData[displaySet]).map((metric) => (
                <Grid item key={metric} sx={{ px: 5, py: 1, width: "100%" }}>
                  <Typography variant="p">{metric}</Typography>
                  <Typography variant="p" sx={{ float: "right" }}>
                    {runData[displaySet][metric].toFixed(2)}
                  </Typography>
                  <Divider sx={{ mt: 1 }} />
                </Grid>
              ))
            )}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

RunMetricsTab.propTypes = {
  runData: PropTypes.shape({
    status: PropTypes.number,
    train_metrics: PropTypes.object,
    test_metrics: PropTypes.object,
    validation_metrics: PropTypes.object,
  }),
  setUpdateDataFlag: PropTypes.func.isRequired,
};

export default RunMetricsTab;
