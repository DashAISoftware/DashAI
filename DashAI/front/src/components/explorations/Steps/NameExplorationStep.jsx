import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { TextField, Grid, Typography } from "@mui/material";

import { useExplorationsContext } from "../context";

function NameExplorationStep({ onValidation = () => {} }) {
  const { explorationData, setExplorationData } = useExplorationsContext();
  const { name, description } = explorationData;

  const [nameOk, setNameOk] = useState(false);
  const [nameError, setNameError] = useState(false);

  useEffect(() => {
    if (name.length >= 4) {
      setNameOk(true);
      setNameError(false);
    } else {
      setNameOk(false);
      setNameError(true);
    }
  }, [name]);

  useEffect(() => {
    if (nameOk) {
      onValidation(true);
    } else {
      onValidation(false);
    }
  }, [nameOk]);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      {/* Set Name subcomponent */}
      <Grid item xs={12}>
        <Typography variant="subtitle1" component="h3">
          Enter a name and description for the new exploration
        </Typography>

        <TextField
          label="Exploration Name"
          autoFocus
          value={name}
          onChange={(e) =>
            setExplorationData((prev) => ({
              ...prev,
              name: e.target.value,
            }))
          }
          autoComplete="off"
          helperText="The exploration name must have at least 4 alphanumeric characters."
          fullWidth
          margin="normal"
          error={nameError}
        />
      </Grid>

      <Grid item xs={12}>
        <TextField
          label="Description"
          value={description}
          onChange={(e) =>
            setExplorationData((prev) => ({
              ...prev,
              description: e.target.value,
            }))
          }
          fullWidth
          margin="normal"
          multiline
          rows={4}
        />
      </Grid>
    </Grid>
  );
}

NameExplorationStep.propTypes = {
  onValidation: PropTypes.func,
};

export default NameExplorationStep;
