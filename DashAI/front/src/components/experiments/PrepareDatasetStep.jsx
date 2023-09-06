import React from "react";
import PropTypes from "prop-types";

import {
  Grid,
  TextField,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
} from "@mui/material";
function PrepareDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  return (
    <React.Fragment>
      <Grid container spacing={1}>
        <Grid item xs={12}>
          <Typography item variant="subtitle1" component="h3" sx={{ mb: 0 }}>
            Choose which columns to use
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Typography
            item
            variant="caption"
            component="h3"
            sx={{ mb: 2, color: "grey" }}
          >
            Ex: 1-6, 23-108
          </Typography>
        </Grid>

        <TextField
          required
          id="dataset-input-columns"
          label="Input"
          fullWidth
          autoComplete="off"
          sx={{ mb: 2 }}
        />
        <TextField
          required
          id="dataset-output-columns"
          label="Output"
          fullWidth
          autoComplete="off"
          sx={{ mb: 2 }}
        />
        <Typography variant="subtitle1" component="h3" sx={{ mb: 2 }}>
          Choose how you wanna divide the dataset for the experiment
        </Typography>
        <RadioGroup
          aria-labelledby="demo-radio-buttons-group-label"
          defaultValue="random-by-percentage"
          name="radio-buttons-group"
        >
          <FormControlLabel
            value="random-by-percentage"
            control={<Radio />}
            label="Random rows by percentage"
          />
          <Grid container direction="row" spacing={4}>
            <Grid item sx={{ xs: 4 }}>
              <TextField id="training" label="Training" autoComplete="off" />
            </Grid>
            <Grid item sx={{ xs: 4 }}>
              <TextField
                id="validation"
                label="Validation"
                autoComplete="off"
              />
            </Grid>
            <Grid item sx={{ xs: 4 }}>
              <TextField id="testing" label="Testing" autoComplete="off" />
            </Grid>
          </Grid>
          <FormControlLabel
            value="default-partitions"
            control={<Radio />}
            label="Default partitions"
          />
          <FormControlLabel
            value="introduce-manually"
            control={<Radio />}
            label="Introduce rows manually"
          />
        </RadioGroup>
      </Grid>
    </React.Fragment>
  );
}

PrepareDatasetStep.propTypes = {
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
export default PrepareDatasetStep;
