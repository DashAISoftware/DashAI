import React, { useState } from "react";
import PropTypes from "prop-types";

import {
  Grid,
  TextField,
  Typography,
  RadioGroup,
  FormControlLabel,
  FormHelperText,
  Radio,
} from "@mui/material";
function PrepareDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  // TODO: column and row numbers should be minor to the maximum on the dataset
  const totalColumns = 100;
  const totalRows = 2000;
  // columns numbers state
  const [inputColumns, setInputColumns] = useState([]);
  const [outputColumns, setOutputColumns] = useState([]);

  // handle columns numbers change state
  const [parseInputColumnsError, setParseInputColumnsError] = useState(false);
  const [parseOutputColumnsError, setParseOutputColumnsError] = useState(false);
  const [parseInputColumnsErrorText, setParseInputColumnsErrorText] =
    useState("");
  const [parseOutputColumnsErrorText, setParseOutputColumnsErrorText] =
    useState("");
  const rangeRegex = /^(\d+)(-(\d+))*(,(\d+)(-(\d+))*)*$/;

  // rows numbers state
  const defaultParitionsIndex = {
    training: [],
    validation: [],
    testing: [],
  };
  const defaultPartitionsPercentage = {
    training: 0,
    validation: 0,
    testing: 0,
  };
  const [rowsPartitionsIndex, setRowsPartitionsIndex] = useState(
    defaultParitionsIndex,
  );
  const [rowsPartitionsPercentage, setRowsPartitionsPercentage] = useState(
    defaultPartitionsPercentage,
  );

  // handle rows numbers change state
  const [rowsPreference, setRowsPreference] = useState("random");
  const [rowsPartitionsError, setRowsPartitionsError] = useState(false);
  const [rowsPartitionsErrorText, setRowsPartitionsErrorText] = useState("");

  const parseRangeToIndex = (value, total) => {
    const numbersArray = [];
    if (!rangeRegex.test(value)) {
      throw new Error(
        "Ranges and indexes must match the format on the example above",
      );
    }
    const ranges = value.split(",");
    ranges.forEach((range) => {
      const [min, max] = range.split("-");
      if (!range.includes("-") && parseInt(range) <= total) {
        numbersArray.push(parseInt(range));
      } else if (
        (!range.includes("-") && parseInt(range) > total) ||
        parseInt(max) > total
      ) {
        throw new Error(
          "The indexes should be minor than the total of columns or rows",
        );
      } else if (parseInt(min) > parseInt(max)) {
        throw new Error(
          "The second number of a range must be greater than the first",
        );
      } else {
        for (let i = parseInt(min); i <= parseInt(max); i++) {
          numbersArray.push(i);
        }
      }
    });
    return numbersArray;
  };

  const checkSplit = (training, validation, testing) => {
    if (parseInt(training) + parseInt(validation) + parseInt(testing) === 100) {
      return true;
    } else {
      return false;
    }
  };
  const handleInputColumnsChange = (event) => {
    const input = event.target.value.replace(/ /g, ""); // TODO: dont accept spaces between numbers
    try {
      const columnNumbers = parseRangeToIndex(input, totalColumns);
      setParseInputColumnsError(false);
      setInputColumns(columnNumbers);
      console.log(inputColumns);
    } catch (error) {
      setParseInputColumnsErrorText(error.message);
      setParseInputColumnsError(true);
    }
  };
  const handleOutputColumnsChange = (event) => {
    const input = event.target.value.replace(/ /g, "");
    try {
      const columnIndex = parseRangeToIndex(input, totalColumns); // TODO: input and output columns should be less than total
      setParseOutputColumnsError(false);
      setOutputColumns(columnIndex);
      console.log(outputColumns);
    } catch (error) {
      setParseOutputColumnsErrorText(error.message);
      setParseOutputColumnsError(true);
    }
  };
  const handleRowsPreferenceChange = (event) => {
    if (event.target.value === "manually") {
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
    if (rowsPreference === "manually") {
      try {
        const rowsIndex = parseRangeToIndex(value, totalRows);
        setRowsPartitionsIndex(
          id === "training"
            ? { ...rowsPartitionsIndex, training: rowsIndex }
            : id === "validation"
            ? { ...rowsPartitionsIndex, validation: rowsIndex }
            : { ...rowsPartitionsIndex, testing: rowsIndex },
        );
        setRowsPartitionsError(false);
      } catch (error) {
        setRowsPartitionsErrorText(error.message);
        setRowsPartitionsError(true);
      }
    } else {
      const newSplits =
        id === "training"
          ? { ...rowsPartitionsPercentage, training: value }
          : id === "validation"
          ? { ...rowsPartitionsPercentage, validation: value }
          : { ...rowsPartitionsPercentage, testing: value };
      setRowsPartitionsPercentage(newSplits);
      if (
        !checkSplit(newSplits.training, newSplits.validation, newSplits.testing)
      ) {
        setRowsPartitionsErrorText("Splits should add 100%");
        setRowsPartitionsError(true);
      } else {
        setRowsPartitionsError(false);
      }
    }
  };

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
          onChange={handleInputColumnsChange}
          error={parseInputColumnsError}
          helperText={parseInputColumnsError ? parseInputColumnsErrorText : ""}
          sx={{ mb: 2 }}
        />
        <TextField
          required
          id="dataset-output-columns"
          label="Output"
          fullWidth
          autoComplete="off"
          onChange={handleOutputColumnsChange}
          error={parseOutputColumnsError}
          helperText={
            parseOutputColumnsError ? parseOutputColumnsErrorText : ""
          }
          sx={{ mb: 2 }}
        />
        <Grid container spacing={1}>
          <Grid item xs={12}>
            <Typography variant="subtitle1" component="h3" sx={{ mb: 2 }}>
              Choose how you wanna divide the dataset for the experiment
            </Typography>
          </Grid>
        </Grid>
        <RadioGroup
          aria-labelledby="demo-radio-buttons-group-label"
          defaultValue={"random"}
          name="radio-buttons-group"
          onChange={handleRowsPreferenceChange}
        >
          <FormControlLabel
            value="random"
            control={<Radio />}
            label="Use random rows by percentage"
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
            value="manually"
            control={<Radio />}
            label="Introduce splits manually by rows index"
          />
          {rowsPreference === "manually" ? (
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
