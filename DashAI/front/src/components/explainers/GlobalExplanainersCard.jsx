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
export default function GlobalExplainersCard({ explainer, scope }) {
  function plotName(name) {
    return name.match(/[A-Z][a-z]+|[0-9]+/g).join(" ");
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
            <Typography variant="h6">
              {plotName(explainer.explainer_name)} Plot
            </Typography>
            <Typography variant="h7">
              Explainer name: {explainer.name}
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
        <GlobalExplainersPlot explainer={explainer} scope={scope} />
      </Grid>
    </Paper>
  );
}

// Duda: por qué algunas están en camelCase?
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
    plot_path: PropTypes.string,
    name: PropTypes.string,
    created: PropTypes.string,
  }).isRequired,
  scope: PropTypes.string.isRequired,
};
