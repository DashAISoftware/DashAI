import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { parseRangeToIndex } from "../../utils/parseRange";
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
  datasetInfo,
  rowsPartitionsIndex,
  setRowsPartitionsIndex,
  rowsPartitionsPercentage,
  setRowsPartitionsPercentage,
  setSplitsReady,
  isRandom,
  setIsRandom,
}) {
  const totalRows = datasetInfo.total_rows;

  // handle rows numbers change state
  const [rowsPartitionsError, setRowsPartitionsError] = useState(false);
  const [rowsPartitionsErrorText, setRowsPartitionsErrorText] = useState("");

  const checkSplit = (train, validation, test) => {
    return train + validation + test === 1;
  };

  const handleRowsPreferenceChange = (event) => {
    if (event.target.value === "splitByIndex") {
      setIsRandom(false);
      setRowsPartitionsPercentage({ train: 70, test: 20, validation: 10 });
    } else {
      setIsRandom(true);
      setRowsPartitionsIndex({ train: [], test: [], validation: [] });
    }
    setRowsPartitionsError(false);
    setRowsPartitionsErrorText("");
  };

  const handleRowsChange = (event) => {
    const value = event.target.value;
    const id = event.target.id; // TODO: check that the training, validation and testing rows dont overlap
    if (isRandom === false) {
      try {
        const rowsIndex = parseRangeToIndex(value, totalRows);
        switch (id) {
          case "train":
            setRowsPartitionsIndex({
              ...rowsPartitionsIndex,
              train: rowsIndex,
            });
            break;
          case "validation":
            setRowsPartitionsIndex({
              ...rowsPartitionsIndex,
              validation: rowsIndex,
            });
            break;
          case "test":
            setRowsPartitionsIndex({
              ...rowsPartitionsIndex,
              test: rowsIndex,
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
        case "train":
          newSplit = { ...newSplit, train: parseFloat(value) };
          break;
        case "validation":
          newSplit = { ...newSplit, validation: parseFloat(value) };
          break;
        case "test":
          newSplit = { ...newSplit, test: parseFloat(value) };
          break;
      }
      setRowsPartitionsPercentage(newSplit);
      if (!checkSplit(newSplit.train, newSplit.validation, newSplit.test)) {
        setRowsPartitionsErrorText(
          "Splits should be numbers between 0 and 1 and should add 1 in total",
        );
        setRowsPartitionsError(true);
      } else {
        setRowsPartitionsError(false);
      }
    }
  };

  useEffect(() => {
    // check if splits doesnt have errors and arent empty
    if (
      isRandom === false &&
      !rowsPartitionsError &&
      rowsPartitionsIndex.train.length >= 1 &&
      rowsPartitionsIndex.validation.length >= 1 &&
      rowsPartitionsIndex.test.length >= 1
    ) {
      setSplitsReady(true);
    } else if (
      isRandom === true &&
      !rowsPartitionsError &&
      rowsPartitionsPercentage.train > 0 &&
      rowsPartitionsPercentage.validation > 0 &&
      rowsPartitionsPercentage.test > 0
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
          label="Use random rows by specifying wich portion of the dataset you want to use for each subset"
          sx={{ my: 1 }}
        />
        {isRandom === true ? (
          <React.Fragment>
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="train"
                  label="Train"
                  autoComplete="off"
                  type="number"
                  size="small"
                  error={rowsPartitionsError}
                  defaultValue={rowsPartitionsPercentage.train}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  type="number"
                  size="small"
                  error={rowsPartitionsError}
                  defaultValue={rowsPartitionsPercentage.validation}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="test"
                  label="Test"
                  type="number"
                  size="small"
                  autoComplete="off"
                  error={rowsPartitionsError}
                  defaultValue={rowsPartitionsPercentage.test}
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
        {isRandom === false ? (
          <React.Fragment>
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="train"
                  label="Train"
                  autoComplete="off"
                  size="small"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  size="small"
                  error={rowsPartitionsError}
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="test"
                  label="Test"
                  autoComplete="off"
                  size="small"
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
  datasetInfo: PropTypes.shape({
    test_size: PropTypes.number,
    total_columns: PropTypes.number,
    total_rows: PropTypes.number,
    train_size: PropTypes.number,
    val_size: PropTypes.number,
  }),
  rowsPartitionsIndex: PropTypes.shape({
    train: PropTypes.arrayOf(PropTypes.number),
    validation: PropTypes.arrayOf(PropTypes.number),
    test: PropTypes.arrayOf(PropTypes.number),
  }),
  setRowsPartitionsIndex: PropTypes.func.isRequired,
  rowsPartitionsPercentage: PropTypes.shape({
    train: PropTypes.number,
    validation: PropTypes.number,
    test: PropTypes.number,
  }),
  setRowsPartitionsPercentage: PropTypes.func.isRequired,
  setSplitsReady: PropTypes.func.isRequired,
  isRandom: PropTypes.bool,
  setIsRandom: PropTypes.func.isRequired,
};
export default SplitDatasetRows;
