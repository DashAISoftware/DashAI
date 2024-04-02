import React from "react";
import PropTypes from "prop-types";
import { Grid, Typography } from "@mui/material";
import ResultsTabParametersList from "./ResultsTabParametersList";

function ResultsTabParametersDisplay({ displayMode, runData }) {

  return (
    <Grid item>
        {displayMode === "nested-list" && (
          <ResultsTabParametersList name="Parameters" value={runData.parameters} />
        )}

        {displayMode === "json" && (
          <Typography variant="body1" component="pre">
            {JSON.stringify(runData.parameters, null, 4)}
          </Typography>
        )}
      </Grid>
  );
}

ResultsTabParametersDisplay.propTypes = {
    displayMode: PropTypes.oneOf(["nested-list", "json"]).isRequired,
    runData: PropTypes.shape({
      parameters: PropTypes.objectOf(
        PropTypes.oneOfType([
          PropTypes.string,
          PropTypes.number,
          PropTypes.bool,
          PropTypes.object,
        ])
      ),
    }).isRequired,
  };

export default ResultsTabParametersDisplay;
