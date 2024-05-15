import { Divider, Grid, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const explainerInfo = [
  { key: "id", label: "Explainer ID" },
  { key: "name", label: "Name" },
  { key: "run_id", label: "Run ID" },
  { key: "explainer_name", label: "Explainer Name" },
  { key: "dataset_id", label: "Dataset ID" },
  { key: "explanation_path", label: "Explanation Path" },
  { key: "plot_path", label: "Plot Path" },
  { key: "status", label: "Status" },
];

const explainerDateInfo = [{ key: "created", label: "Created" }];

const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  const options = {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    locale: "en-US",
  };

  return date.toLocaleString("en-US", options);
};
/**
 * Component that displays general information associated with a explainer.
 * @param {object} explainerData object that contains all the necesary info of the explainer
 */
function ExplainerInfoTab({ explainerData }) {
  return (
    <Grid container direction="column">
      {/* Explainer name related info */}
      <Grid item>
        <Grid
          container
          direction="row"
          alignItems="center"
          rowSpacing={3}
          columnSpacing={15}
        >
          {explainerInfo.map((param) => (
            <Grid item key={param.key}>
              <Typography variant="subtitle1">{param.label}</Typography>
              <Typography variant="p" sx={{ color: "gray" }}>
                {explainerData[param.key] ?? "-"}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </Grid>

      <Divider sx={{ mt: 3, mb: 3 }} />

      {/* Explainer Date related info */}
      <Grid item>
        <Grid
          container
          direction="row"
          alignItems="center"
          rowSpacing={3}
          columnSpacing={15}
        >
          {explainerDateInfo.map((param) => (
            <Grid item key={param.key}>
              <Typography variant="subtitle1">{param.label}</Typography>
              <Typography variant="p" sx={{ color: "gray" }}>
                {formatDate(explainerData[param.key] ?? "-")}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </Grid>
    </Grid>
  );
}

ExplainerInfoTab.propTypes = {
  explainerData: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    run_id: PropTypes.number,
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    explanation_path: PropTypes.string,
    plot_path: PropTypes.string,
    parameters: PropTypes.object,
    created: PropTypes.string,
    status: PropTypes.number,
  }).isRequired,
};

export default ExplainerInfoTab;
