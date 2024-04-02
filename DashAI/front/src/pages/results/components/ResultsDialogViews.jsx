import React from "react";
import PropTypes from "prop-types";
import { Grid, Button, Typography } from "@mui/material";

function ResultsDialogViews({ showTable, handleShowTable, handleShowGraphs }) {
  return (
    <Grid container direction="column" alignItems="center">
      <Grid item container justifyContent="flex-start" sx={{ mt: 2, mb: 1 }}>
        <Grid item sx={{ ml: 2 }}>
          <Typography variant="body1">
            View results as columns or graphs
          </Typography>
        </Grid>
      </Grid>
      <Grid item sx={{ my: 1 }}>
        <Grid container justifyContent="center">
          <Button
            variant="contained"
            color={showTable ? "primary" : "inherit"}
            onClick={handleShowTable}
            style={{
              border: showTable ? "2px solid #00bebb" : "2px solid #00bebb",
              color: showTable ? "#ffffff" : "#00bebb",
              borderRadius: "1px",
            }}
          >
            Columns
          </Button>
          <Button
            variant="contained"
            color={!showTable ? "primary" : "inherit"}
            onClick={handleShowGraphs}
            style={{
              border: !showTable ? "2px solid #00bebb" : "2px solid #00bebb",
              color: !showTable ? "#ffffff" : "#00bebb",
              borderRadius: "1px",
            }}
          >
            Graphs
          </Button>
        </Grid>
      </Grid>
    </Grid>
  );
}

ResultsDialogViews.propTypes = {
  showTable: PropTypes.bool.isRequired,
  handleShowTable: PropTypes.func.isRequired,
  handleShowGraphs: PropTypes.func.isRequired,
};

export default ResultsDialogViews;
