import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Grid, Paper, TextField, Typography } from "@mui/material";

function SetExperimentName({ newExp, setNewExp, setNextEnabled }) {
  const [nModifications, setNModifications] = useState(0);
  const [error, setError] = useState(false);

  const handleNameInputChange = (event) => {
    setNewExp({ ...newExp, name: event.target.value });
    setNModifications(nModifications + 1);

    if (nModifications + 1 > 4) {
      if (event.target.value.length < 4) {
        setError(true);
        setNextEnabled(false);
      } else {
        setError(false);
        setNextEnabled(true);
      }
    }
  };

  // enable the next button if the experiment has already a valid name.
  useEffect(() => {
    if (typeof newExp.name === "string" && newExp.name.length >= 4) {
      setNextEnabled(true);
      setNModifications(4);
    }
  }, []);

  return (
    <Paper sx={{ p: 4, minHeight: "100%" }}>
      <Grid
        container
        direction="column"
        justifyContent="center"
        alignItems="center"
      >
        <Grid item xs={12} sm={10} md={8} lg={6}>
          <Typography variant="h6" component="h3" align="center">
            Choose a name to the new experiment
          </Typography>
          <Typography sx={{ mb: 3, mt: 1 }} align="center">
            {
              "The experiment name must have at least 4 alphanumeric characters."
            }
          </Typography>

          <TextField
            id="experiment-name-input"
            label="Experiment name"
            value={newExp.name}
            fullWidth
            onChange={handleNameInputChange}
            sx={{ mb: 2 }}
            error={error}
            helperText={error && "The name has less than 4 characters!"}
          />
        </Grid>
      </Grid>
    </Paper>
  );
}

SetExperimentName.propTypes = {
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
export default SetExperimentName;
