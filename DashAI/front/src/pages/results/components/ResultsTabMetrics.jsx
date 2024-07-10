import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Grid } from "@mui/material";

import ResultsTabMetricsToggle from "./ResultsTabMetricsToggle";
import ResultsTabMetricsRuns from "./ResultsTabMetricsRuns";

/**
 * Component that displays the metrics associated with a run.
 * @param {object} runData object that contains all the necesary info of the
 */
function ResultsTabMetrics({ runData, setUpdateDataFlag }) {
  const [displaySet, setDisplaySet] = useState("test_metrics");

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
      <ResultsTabMetricsToggle
        displaySet={displaySet}
        setDisplaySet={setDisplaySet}
      />

      {/* metrics */}
      <ResultsTabMetricsRuns runData={runData} displaySet={displaySet} />
    </Grid>
  );
}

ResultsTabMetrics.propTypes = {
  runData: PropTypes.shape({
    status: PropTypes.number,
    train_metrics: PropTypes.object,
    test_metrics: PropTypes.object,
    validation_metrics: PropTypes.object,
  }),
  setUpdateDataFlag: PropTypes.func.isRequired,
};

export default ResultsTabMetrics;
