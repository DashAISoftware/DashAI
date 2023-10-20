import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import {
  Grid,
  TextField,
  Typography,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormHelperText,
} from "@mui/material";

function SplitDatasetRows({
  rowsPartitionsIndex,
  setRowsPartitionsIndex,
  rowsPartitionsPercentage,
  setRowsPartitionsPercentage,
  setSplitsReady,
  parseRangeToIndex,
}) {
  const totalRows = 2000;
  const defaultParitionsIndex = {
    training: [],
    validation: [],
    testing: [],
  };
  const defaultPartitionsPercentage = {
    training: 60,
    validation: 20,
    testing: 20,
  };

  // handle rows numbers change state
  const [rowsPreference, setRowsPreference] = useState("random");
  const [rowsPartitionsError, setRowsPartitionsError] = useState(false);
  const [rowsPartitionsErrorText, setRowsPartitionsErrorText] = useState("");

  const checkSplit = (training, validation, testing) => {
    return training + validation + testing === 100;
  };

  const handleRowsPreferenceChange = (event) => {
    if (event.target.value === "splitByIndex") {
      setRowsPartitionsPercentage(defaultPartitionsPercentage);
    } else {
      setRowsPartitionsIndex(defaultParitionsIndex);
    }
    setRowsPartitionsError(false);
    setRowsPartitionsErrorText("");
    setRowsPreference(event.target.value);
  };

  const handleRowsChange = (event) => {
    const value = event.target.value;
    const id = event.target.id; // TODO: check that the training, validation and testing rows dont overlap
    if (rowsPreference === "splitByIndex") {
      try {
        const rowsIndex = parseRangeToIndex(value, totalRows);
        switch (id) {
          case "training":
            setRowsPartitionsIndex({
              ...rowsPartitionsIndex,
              training: rowsIndex,
            });
            break;
          case "validation":
            setRowsPartitionsIndex({
              ...rowsPartitionsIndex,
              validation: rowsIndex,
            });
            break;
          case "testing":
            setRowsPartitionsIndex({
              ...rowsPartitionsIndex,
              testing: rowsIndex,
            });
            break;
        }
        setRowsPartitionsError(false);
      } catch (error) {
        setRowsPartitionsErrorText(error.message);
        setRowsPartitionsError(true);
      }
    } else {
      let newSplit = rowsPartitionsPercentage;
      switch (id) {
        case "training":
          newSplit = { ...newSplit, training: parseInt(value) };
          break;
        case "validation":
          newSplit = { ...newSplit, validation: parseInt(value) };
          break;
        case "testing":
          newSplit = { ...newSplit, testing: parseInt(value) };
          break;
      }
      setRowsPartitionsPercentage(newSplit);
      if (
        !checkSplit(newSplit.training, newSplit.validation, newSplit.testing)
      ) {
        setRowsPartitionsErrorText("Splits should add 100%");
        setRowsPartitionsError(true);
      } else {
        setRowsPartitionsError(false);
      }
    }
  };

  useEffect(() => {
    // check if splits doesnt have errors and arent empty
    if (
      rowsPreference === "splitByIndex" &&
      !rowsPartitionsError &&
      rowsPartitionsIndex.training.length >= 1 &&
      rowsPartitionsIndex.validation.length >= 1 &&
      rowsPartitionsIndex.testing.length >= 1
    ) {
      setSplitsReady(true);
    } else if (
      rowsPreference === "random" &&
      !rowsPartitionsError &&
      rowsPartitionsPercentage.training > 0 &&
      rowsPartitionsPercentage.validation > 0 &&
      rowsPartitionsPercentage.testing > 0
    ) {
      setSplitsReady(true);
    } else {
      setSplitsReady(false);
    }
  }, [rowsPartitionsIndex, rowsPartitionsPercentage, rowsPartitionsError]);
  return (
    <React.Fragment>
      <Grid container spacing={1}>
        <Grid item xs={12}>
          <Typography variant="subtitle1" component="h3" sx={{ mb: 2 }}>
            Select how to divide the dataset into training, validation and test
            subsets.
          </Typography>
        </Grid>
      </Grid>
      <RadioGroup
        defaultValue={"random"}
        name="radio-buttons-group"
        onChange={handleRowsPreferenceChange}
      >
        <FormControlLabel
          value="random"
          control={<Radio />}
          label="Use random rows by percentage"
          sx={{ my: 1 }}
        />
        {rowsPreference === "random" ? (
          <React.Fragment>
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="training"
                  label="Training"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="testing"
                  label="Testing"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
            </Grid>
            {rowsPartitionsError ? (
              <FormHelperText>{rowsPartitionsErrorText}</FormHelperText>
            ) : (
              <React.Fragment />
            )}
          </React.Fragment>
        ) : (
          <React.Fragment />
        )}
        <FormControlLabel
          value="splitByIndex"
          control={<Radio />}
          label="Use manual splitting by specifying the row indexes of each subset"
          sx={{ my: 1 }}
        />
        {rowsPreference === "splitByIndex" ? (
          <React.Fragment>
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="training"
                  label="Training"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="testing"
                  label="Testing"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
            </Grid>
            {rowsPartitionsError ? (
              <FormHelperText>{rowsPartitionsErrorText}</FormHelperText>
            ) : (
              <React.Fragment />
            )}
          </React.Fragment>
        ) : (
          <React.Fragment />
        )}
      </RadioGroup>
    </React.Fragment>
  );
}

SplitDatasetRows.propTypes = {
  rowsPartitionsIndex: PropTypes.shape({
    training: PropTypes.arrayOf(PropTypes.number),
    validation: PropTypes.arrayOf(PropTypes.number),
    testing: PropTypes.arrayOf(PropTypes.number),
  }),
  setRowsPartitionsIndex: PropTypes.func.isRequired,
  rowsPartitionsPercentage: PropTypes.shape({
    training: PropTypes.number,
    validation: PropTypes.number,
    testing: PropTypes.number,
  }),
  setRowsPartitionsPercentage: PropTypes.func.isRequired,
  setSplitsReady: PropTypes.func.isRequired,
  parseRangeToIndex: PropTypes.func.isRequired,
};
export default SplitDatasetRows;
