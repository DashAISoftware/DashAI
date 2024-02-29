import React from "react";
import { Grid, Typography, IconButton, Paper } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import PropTypes from "prop-types";
import GlobalExplainersPlot from "./GlobalExplainersPlot";

/**
 * GlobalExplainersCard
 * @param {*} explainer
 * @returns Component that render a card for the explainer
 */
export default function GlobalExplainersCard({ explainer }) {
  function plotName(name) {
    switch (name) {
      case "PartialDependence":
        return "Partial Dependence";
      case "PermutationFeatureImportance":
        return "Permutation Feature Importance";
    }
  }

  return (
    <Paper elevation={3}>
      <Grid container item minWidth={800} maxWidth={800} p={4} gap={2}>
        <Grid
          item
          container
          direction={"row"}
          justifyContent={"space-between"}
          alignItems={"center"}
        >
          <Grid item>
            <Typography variant="h6">{`GlobalExplainer${explainer.id}`}</Typography>
            <Typography variant="h6">
              {plotName(explainer.explainer_name)} Plot
            </Typography>
          </Grid>
          <Grid item>
            <IconButton aria-label="zoomin">
              <ZoomInIcon />
            </IconButton>
            <IconButton aria-label="delete" color="error">
              <DeleteIcon />
            </IconButton>
          </Grid>
        </Grid>
        <GlobalExplainersPlot explainerType={explainer.explainer_name} />
      </Grid>
    </Paper>
  );
}

GlobalExplainersCard.propTypes = {
  explainer: PropTypes.shape({
    explainer_name: PropTypes.string,
    id: PropTypes.number,
    parameters: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string,
        PropTypes.arrayOf(PropTypes.string),
      ]),
    ),
    status: PropTypes.number,
    runId: PropTypes.number,
    explanationPath: PropTypes.string,
    name: PropTypes.string,
    created: PropTypes.string,
  }).isRequired,
};
