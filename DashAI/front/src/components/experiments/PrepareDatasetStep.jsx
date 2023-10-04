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
  const [rowsPartitionsNumbers, setRowsPartitionsNumbers] = useState({
    training: [],
    validation: [],
    testing: [],
  });
  const [rowsPartitionsPercentage, setRowsPartitionsPercentage] = useState({
    training: 0,
    validation: 0,
    testing: 0,
  });

  // handle rows numbers change state
  const [rowsPreference, setRowsPreference] = useState("default-partitions");
  const [rowsPartitionsError, setRowsPartitionsError] = useState(false);
  const [rowsPartitionsErrorText, setRowsPartitionsErrorText] = useState("");

  const parseRangeToNumbers = (value) => {
    const numbersArray = [];
    if (!rangeRegex.test(value)) {
      throw new Error(
        "Range and numbers must match the format on the example above",
      );
    }
    const ranges = value.split(",");
    ranges.forEach((range) => {
      const [min, max] = range.split("-");
      if (!range.includes("-")) {
        numbersArray.push(parseInt(range));
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

  const handleInputColumnsChange = (event) => {
    const input = event.target.value.replace(/ /g, ""); // todo: dont accept spaces between numbers
    try {
      const columnNumbers = parseRangeToNumbers(input);
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
      const columnNumbers = parseRangeToNumbers(input);
      setParseOutputColumnsError(false);
      setOutputColumns(columnNumbers);
      console.log(outputColumns);
    } catch (error) {
      setParseOutputColumnsErrorText(error.message);
      setParseOutputColumnsError(true);
    }
  };
  const handleRowsPreferenceChange = (event) => {
    setRowsPreference(event.target.value); // clean numbers for the other preference?
  };

  const handleRowsChange = (event) => {
    const value = event.target.value;
    const id = event.target.id;
    if (rowsPreference === "introduce-manually") {
      try {
        const trainingRowsNumbers = parseRangeToNumbers(value);
        setRowsPartitionsNumbers(
          id === "training"
            ? { ...rowsPartitionsNumbers, training: trainingRowsNumbers }
            : id === "validation"
            ? { ...rowsPartitionsNumbers, validation: trainingRowsNumbers }
            : { ...rowsPartitionsNumbers, testing: trainingRowsNumbers },
        );
        console.log(rowsPartitionsNumbers);
        setRowsPartitionsError(false);
      } catch (error) {
        setRowsPartitionsErrorText(error.message);
        setRowsPartitionsError(true);
      }
    } else {
      // todo: check if adds 1 if not throw error
      setRowsPartitionsPercentage(
        id === "training"
          ? { ...rowsPartitionsNumbers, training: value }
          : id === "validation"
          ? { ...rowsPartitionsNumbers, validation: value }
          : { ...rowsPartitionsNumbers, testing: value },
      );
      console.log(rowsPartitionsPercentage);
      setRowsPartitionsError(false);
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
        <Typography variant="subtitle1" component="h3" sx={{ mb: 2 }}>
          Choose how you wanna divide the dataset for the experiment
        </Typography>
        <RadioGroup
          aria-labelledby="demo-radio-buttons-group-label"
          defaultValue={
            rowsPreference === "default-partitions"
              ? "default-partitions"
              : "random-by-percentage"
          }
          name="radio-buttons-group"
          onChange={handleRowsPreferenceChange}
        >
          {rowsPartitionsError ? (
            <FormHelperText>{rowsPartitionsErrorText}</FormHelperText>
          ) : (
            <React.Fragment />
          )}
          <FormControlLabel
            value="random-by-percentage"
            control={<Radio />}
            label="Random rows by percentage"
          />
          {rowsPreference === "random-by-percentage" ? (
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="training"
                  label="Training"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="testing"
                  label="Testing"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
            </Grid>
          ) : (
            <React.Fragment />
          )}
          <FormControlLabel
            value="default-partitions"
            control={<Radio />}
            label="Default partitions"
          />
          {rowsPreference === "default-partitions" ? (
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="training"
                  label="Training"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="testing"
                  label="Testing"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
            </Grid>
          ) : (
            <React.Fragment />
          )}
          <FormControlLabel
            value="introduce-manually"
            control={<Radio />}
            label="Introduce rows manually"
          />
          {rowsPreference === "introduce-manually" ? (
            <Grid container direction="row" spacing={4}>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="training"
                  label="Training"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="validation"
                  label="Validation"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
              <Grid item sx={{ xs: 4 }}>
                <TextField
                  id="testing"
                  label="Testing"
                  autoComplete="off"
                  onChange={handleRowsChange}
                />
              </Grid>
            </Grid>
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
