import React from "react";
import { DialogContentText, Grid, Paper } from "@mui/material";
import PropTypes from "prop-types";

import ParameterForm from "../configurableObject/ParameterForm";

function ExplainerConfiguration({ paramsSchema, updateParameters }) {
  return (
    <Paper
      variant="outlined"
      sx={{ p: 4, maxHeight: "55vh", overflow: "auto" }}
    >
      <Grid container direction={"column"} alignItems={"center"}>
        {/* Form title */}
        <Grid item>
          <DialogContentText>Explainer configuration</DialogContentText>
        </Grid>
        <Grid item sx={{ p: 3 }}>
          {/* Main dataloader form */}
          <ParameterForm
            parameterSchema={paramsSchema}
            onFormSubmit={updateParameters}
          />
        </Grid>
      </Grid>
    </Paper>
  );
}

ExplainerConfiguration.propTypes = {
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  updateParameters: PropTypes.func,
};

export default ExplainerConfiguration;
