import React from "react";
import PropTypes from "prop-types";
import { Grid, Typography } from "@mui/material";

import { runNameInfo } from "../constants/runNameInfo";

function ResultsTabInfoName({ runData }) {

  return (
    <Grid item>
        <Grid
          container
          direction="row"
          alignItems="center"
          rowSpacing={3}
          columnSpacing={15}
        >
          {runNameInfo.map((param) => (
            <Grid item key={param.key}>
              <Typography variant="subtitle1">{param.label}</Typography>
              <Typography variant="p" sx={{ color: "gray" }}>
                {runData[param.key] ?? "-"}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </Grid>
  );
}

ResultsTabInfoName.propTypes = {
    runData: PropTypes.object.isRequired,
};

export default ResultsTabInfoName;
