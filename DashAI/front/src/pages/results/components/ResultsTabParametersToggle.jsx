import React from "react";
import PropTypes from "prop-types";
import { Grid, ToggleButton, ToggleButtonGroup } from "@mui/material";

function ResultsTabParametersToggle({ displayMode, setDisplayMode }) {
  return (
    <Grid item>
      <ToggleButtonGroup
        value={displayMode}
        exclusive
        onChange={(event, newMode) => {
          if (newMode !== null) {
            setDisplayMode(newMode);
          }
        }}
        sx={{ float: "right" }}
      >
        <ToggleButton value="nested-list">List</ToggleButton>
        <ToggleButton value="json">JSON</ToggleButton>
      </ToggleButtonGroup>
    </Grid>
  );
}

ResultsTabParametersToggle.propTypes = {
  displayMode: PropTypes.oneOf(["nested-list", "json"]).isRequired,
  setDisplayMode: PropTypes.func.isRequired,
};

export default ResultsTabParametersToggle;
