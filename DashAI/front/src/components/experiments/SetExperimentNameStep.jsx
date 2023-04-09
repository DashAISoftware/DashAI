import {
  DialogContentText,
  Grid,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import React from "react";

export default function SetExperimentName() {
  const [expName, setExpName] = React.useState("");
  const [nModifications, setNModifications] = React.useState(0);
  const [error, setError] = React.useState(false);

  const handleChange = (event) => {
    setExpName(event.target.value);
    setNModifications(nModifications + 1);

    if (nModifications + 1 > 4) {
      if (event.target.value.length < 4) {
        setError(true);
      } else {
        setError(false);
      }
    }
  };

  return (
    <DialogContentText id="new-experiment-set-name-step" sx={{ mb: 3 }}>
      <Paper variant="outlined" sx={{ p: 4 }}>
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
              value={expName}
              fullWidth
              onChange={handleChange}
              sx={{ mb: 2 }}
              error={error}
              helperText={error && "The name has less than 4 characters!"}
            />
          </Grid>
        </Grid>
      </Paper>
    </DialogContentText>
  );
}
