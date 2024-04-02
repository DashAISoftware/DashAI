import { Divider, Grid, Typography } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

import ResultsTabInfoName from "./ResultsTabInfoName";
import ResultsTabInfoDate from "./ResultsTabInfoDate";
import ResultsTabInfoDescription from "./ResultsTabInfoDescription";

/**
 * Component that displays general information associated with a run.
 * @param {object} runData object that contains all the necesary info of the run
 */
function ResultsTabInfo({ runData }) {
  return (
    <Grid container direction="column">
      {/* Run name related info */}
      <ResultsTabInfoName runData={runData}/>

      <Divider sx={{ mt: 3, mb: 3 }} />

      {/* Run Date related info */}
      <ResultsTabInfoDate runData={runData}/>

      <Divider sx={{ mt: 3, mb: 3 }} />

      {/* Run description */}
      <ResultsTabInfoDescription runData={runData}/>
    </Grid>
  );
}

ResultsTabInfo.propTypes = {
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

export default ResultsTabInfo;
