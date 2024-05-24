import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { Grid, Typography } from "@mui/material";
import OptimizationTable from "./OptimizationTable";
/**
 * Step of the experiment modal: add models to the experiment and configure its parameters
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 */
function HyperparameterOptimizationStep({ newExp, setNewExp, setNextEnabled }) {
  // checks if there is at least 1 model added to enable the "Next" button
  useEffect(() => {
    if (newExp.runs.length > 0) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [newExp]);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      <Grid item xs={12}>
        <Typography variant="subtitle1" component="h3">
          Add optimizers to your experiment
        </Typography>
      </Grid>
      {/* Hyperparameter Optimization table */}
      <Grid item xs={12}>
        <OptimizationTable newExp={newExp} setNewExp={setNewExp} />
      </Grid>
    </Grid>
  );
}

HyperparameterOptimizationStep.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default HyperparameterOptimizationStep;
