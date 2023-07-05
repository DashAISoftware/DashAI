import React, { useState } from "react";
import PropTypes from "prop-types";
import {
  Grid,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import ParameterListItem from "./ParameterListItem";

/**
 * Component that displays the parameters associated with a run.
 * @param {object} runData object that contains all the necesary info of the
 */
function RunParametersTab({ runData }) {
  const [displayMode, setDisplayMode] = useState("nested-list");
  return (
    <Grid container direction="column">
      {/* Toggle to select the mode of displaying the JSON object. */}
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

      {/* JSON object display */}
      <Grid item>
        {displayMode === "nested-list" && (
          <ParameterListItem name="Parameters" value={runData.parameters} />
        )}

        {displayMode === "json" && (
          <Typography variant="body1" component="pre">
            {JSON.stringify(runData.parameters, null, 4)}
          </Typography>
        )}
      </Grid>
    </Grid>
  );
}

RunParametersTab.propTypes = {
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

export default RunParametersTab;
