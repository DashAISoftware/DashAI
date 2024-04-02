import React from "react";
import PropTypes from "prop-types";
import { Grid, Typography } from "@mui/material";

function ResultsTabInfoDescription({ runData }) {
  return (
    <Grid item>
      <Typography variant="subtitle1">Description</Typography>
      <Typography variant="p" sx={{ color: "gray" }}>
        {runData.description ?? "-"}
      </Typography>
    </Grid>
  );
}

ResultsTabInfoDescription.propTypes = {
  runData: PropTypes.object.isRequired,
};

export default ResultsTabInfoDescription;
