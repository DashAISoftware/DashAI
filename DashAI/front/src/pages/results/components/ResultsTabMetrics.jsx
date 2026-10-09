import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Grid } from "@mui/material";

import ResultsTabMetricsToggle from "./ResultsTabMetricsToggle";
import ResultsTabMetricsRuns from "./ResultsTabMetricsRuns";

/**
 * Component that displays the metrics associated with a run.
 * @param {object} runData object that contains all the necesary info of the
 */
function ResultsTabMetrics({ runData }) {
  const has = (split) =>
    Object.keys(runData?.[`${split}_metrics`] || {}).length > 0;
  const hasTrainData = has("train");
  const hasValidationData = has("validation");
  const hasTestData = has("test");

  // Prefer the reserved rows when the session set some aside; a run without
  // them only has validation estimates to show.
  const [displaySet, setDisplaySet] = useState("test_metrics");

  // The metrics arrive asynchronously, so the split picked above can turn out
  // to be one the run never scored.
  useEffect(() => {
    const available = [
      hasTestData && "test_metrics",
      hasValidationData && "validation_metrics",
      hasTrainData && "train_metrics",
    ].filter(Boolean);
    if (available.length > 0 && !available.includes(displaySet)) {
      setDisplaySet(available[0]);
    }
  }, [hasTrainData, hasValidationData, hasTestData, displaySet]);

  return (
    <Grid container direction="column" rowSpacing={4}>
      {/* Toggle to select the set on which the metrics are applied.  */}
      <ResultsTabMetricsToggle
        displaySet={displaySet}
        setDisplaySet={setDisplaySet}
        hasTrainData={hasTrainData}
        hasValidationData={hasValidationData}
        hasTestData={hasTestData}
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
    evaluation_strategy: PropTypes.string,
  }),
  setUpdateDataFlag: PropTypes.func.isRequired,
};

export default ResultsTabMetrics;
