import React, { useEffect, useState } from "react";
import PropTypes, { number } from "prop-types";

import {
  Grid,
  TextField,
  Typography,
  RadioGroup,
  FormControlLabel,
  FormHelperText,
  Radio,
} from "@mui/material";

/**
 * Step of the experiment modal: Set the input and output columns to use for clasification
 * and the splits for training, validation and testing
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 */
function PrepareDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  // TODO: column and row numbers should be minor to the maximum on the dataset
  const totalColumns = 100;
  const totalRows = 2000;
  // columns numbers state
  const [inputColumns, setInputColumns] = useState([]);
  const [outputColumns, setOutputColumns] = useState([]);
  const [columnsReady, setColumnsReady] = useState(false);

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
    training: 60,
    validation: 20,
    testing: 20,
  };
  const [rowsPartitionsIndex, setRowsPartitionsIndex] = useState(
    defaultParitionsIndex,
  );
  const [rowsPartitionsPercentage, setRowsPartitionsPercentage] = useState(
    defaultPartitionsPercentage,
  );
  const [splitsReady, setSplitsReady] = useState(false);

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
    return parseInt(training) + parseInt(validation) + parseInt(testing) === 100
  };
  const handleInputColumnsChange = (event) => {
    const input = event.target.value.replace(/ /g, ""); // TODO: dont accept spaces between numbers
    try {
      const columnNumbers = parseRangeToIndex(input, totalColumns);
      setParseInputColumnsError(false);
      setInputColumns(columnNumbers);
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
switch (id) {
  case "training":
    setRowsPartitionsIndex({ ...rowsPartitionsIndex, training: rowsIndex });
    break;
  case "validation":
    setRowsPartitionsIndex({ ...rowsPartitionsIndex, validation: rowsIndex });
    break;
  case "test":
    setRowsPartitionsIndex({ ...rowsPartitionsIndex, testing: rowsIndex });
    break;
}
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

  useEffect(() => {
    // check if input and output columns are not empty
    if (
      !parseInputColumnsError &&
      inputColumns.length >= 1 &&
      !parseOutputColumnsError &&
      outputColumns.length >= 1
    ) {
      setColumnsReady(true);
    } else {
      setColumnsReady(false);
    }
  }, [
    inputColumns,
    outputColumns,
    parseInputColumnsError,
    parseOutputColumnsError,
  ]);
  useEffect(() => {
    // check if splits doesnt have errors and arent empty
    if (
      rowsPreference === "manually" &&
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
  useEffect(() => {
    if (columnsReady && splitsReady) {
      setNewExp({
        ...newExp,
        input_columns: inputColumns,
        output_columns: outputColumns,
        splits:
          rowsPreference === "manually"
            ? rowsPartitionsIndex
            : rowsPartitionsPercentage,
      }); // splits should depend on preference
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [columnsReady, splitsReady]);

  return (
    <React.Fragment>
      <Grid container spacing={1}>
        <Grid item xs={12}>
          <Typography item variant="subtitle1" component="h3" sx={{ mb: 0 }}>
            Indicate which columns of the dataset will be used as input and output.
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Typography
            item
            variant="caption"
            component="h3"
            sx={{ mb: 2, color: "grey" }}
          >
            The notation is based on ranges. For example: 1-6, 23-108
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
              Select how to divide the dataset into training, validation and test subsets.
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
    input_columns: PropTypes.arrayOf(Proptypes.number),
    output_columns: PropTypes.arrayOf(Proptypes.number),
    splits: PropTypes.object,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};
export default PrepareDatasetStep;
