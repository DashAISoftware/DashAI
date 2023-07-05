import { Divider, Grid, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const runNameInfo = [
  { key: "name", label: "Name" },
  { key: "model_name", label: "Model Name" },
  { key: "status", label: "Status" },
  { key: "id", label: "Run ID" },
  { key: "experiment_id", label: "Experiment ID" },
  { key: "run_path", label: "Run Path" },
];

const runDateInfo = [
  { key: "created", label: "Created" },
  { key: "last_modified", label: "Last Modified" },
  { key: "delivery_time", label: "Delivery Time" },
  { key: "start_time", label: "Start Time" },
  { key: "end_time", label: "End Time" },
];

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
 * Component that displays general information associated with a run.
 * @param {object} runData object that contains all the necesary info of the run
 */
function RunInfoTab({ runData }) {
  return (
    <Grid container direction="column">
      {/* Run name related info */}
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

      <Divider sx={{ mt: 3, mb: 3 }} />

      {/* Run Date related info */}
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

      <Divider sx={{ mt: 3, mb: 3 }} />

      {/* Run description */}
      <Grid item>
        <Typography variant="subtitle1">Description</Typography>
        <Typography variant="p" sx={{ color: "gray" }}>
          {runData.description ?? "-"}
        </Typography>
      </Grid>
    </Grid>
  );
}

RunInfoTab.propTypes = {
  runData: PropTypes.shape({
    name: PropTypes.string,
    model_name: PropTypes.string,
    status: PropTypes.number,
    id: PropTypes.number,
    experiment_id: PropTypes.number,
    run_path: PropTypes.string,
    created: PropTypes.string,
    last_modified: PropTypes.string,
    delivery_time: PropTypes.string,
    start_time: PropTypes.string,
    end_time: PropTypes.string,
    description: PropTypes.string,
  }).isRequired,
};

export default RunInfoTab;
