import React from "react";
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
  Typography,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { getDisplaySetName } from "../constants/getDisplaySetName";

function ResultsTabMetricsRuns({ runData, displaySet }) {
  return (
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
                  {`There are no metrics associated with the ${getDisplaySetName(
                    displaySet,
                  )} set in this run`}
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
                The result metrics for {getDisplaySetName(displaySet)} set are
                empty.
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
  );
}

ResultsTabMetricsRuns.propTypes = {
  runData: PropTypes.object.isRequired,
  displaySet: PropTypes.string.isRequired,
};

export default ResultsTabMetricsRuns;
