import React from "react";
import PropTypes from "prop-types";
import { Grid, Typography } from "@mui/material";

import { runDateInfo } from "../constants/runDateInfo";
import { formatDate } from "../constants/formatDate";

function ResultsTabInfoDate({ runData }) {
  return (
    <Grid item>
      <Grid
        container
        direction="row"
        alignItems="center"
        rowSpacing={3}
        columnSpacing={15}
      >
        {runDateInfo.map((param) => (
          <Grid item key={param.key}>
            <Typography variant="subtitle1">{param.label}</Typography>
            <Typography variant="p" sx={{ color: "gray" }}>
              {formatDate(runData[param.key] ?? "-")}
            </Typography>
          </Grid>
        ))}
      </Grid>
    </Grid>
  );
}

ResultsTabInfoDate.propTypes = {
  runData: PropTypes.object.isRequired,
};

export default ResultsTabInfoDate;
