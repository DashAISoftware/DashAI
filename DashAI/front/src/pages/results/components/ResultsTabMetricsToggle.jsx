import React from "react";
import PropTypes from "prop-types";
import { Grid, ToggleButton, ToggleButtonGroup } from "@mui/material";

function ResultsTabMetricsToggle({ displaySet, setDisplaySet }) {

  return (
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
  );
}

ResultsTabMetricsToggle.propTypes = {
    displaySet: PropTypes.string.isRequired,
    setDisplaySet: PropTypes.func.isRequired,
  };

export default ResultsTabMetricsToggle;
