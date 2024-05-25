import React, { useState } from "react";
import PropTypes from "prop-types";
import { Grid } from "@mui/material";
import ResultsTabParametersToggle from "./ResultsTabParametersToggle";
import ResultsTabParametersDisplay from "./ResultsTabParametersDisplay";

/**
 * Component that displays the parameters associated with a run.
 * @param {object} runData object that contains all the necesary info of the
 */
function ResultsTabParameters({ runData }) {
  const [displayMode, setDisplayMode] = useState("nested-list");
  return (
    <Grid container direction="column">
      {/* Toggle to select the mode of displaying the JSON object. */}
      <ResultsTabParametersToggle
        displayMode={displayMode}
        setDisplayMode={setDisplayMode}
      />

      {/* JSON object display */}
      <ResultsTabParametersDisplay
        displayMode={displayMode}
        runData={runData}
      />
    </Grid>
  );
}

ResultsTabParameters.propTypes = {
  runData: PropTypes.shape({
    parameters: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ),
  }).isRequired,
};

export default ResultsTabParameters;
