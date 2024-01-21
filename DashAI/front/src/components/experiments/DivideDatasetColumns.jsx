import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { parseRangeToIndex } from "../../utils/parseRange";
import { Grid, TextField, Typography } from "@mui/material";

function DivideDatasetColumns({
  datasetInfo,
  inputColumns,
  setInputColumns,
  outputColumns,
  setOutputColumns,
  setColumnsReady,
}) {
  // TODO: column and row numbers should be minor to the maximum on the dataset
  const totalColumns = datasetInfo.total_columns;

  // handle columns numbers change state
  const [parseInputColumnsError, setParseInputColumnsError] = useState(false);
  const [parseOutputColumnsError, setParseOutputColumnsError] = useState(false);
  const [parseInputColumnsErrorText, setParseInputColumnsErrorText] =
    useState("");
  const [parseOutputColumnsErrorText, setParseOutputColumnsErrorText] =
    useState("");

  const handleInputColumnsChange = (event) => {
    const input = event.target.value.replace(/ /g, ""); // TODO: dont accept spaces between numbers
    try {
      const columnIndex = parseRangeToIndex(input, totalColumns);
      setParseInputColumnsError(false);
      setInputColumns(columnIndex);
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
    // set default input and output columns
    setInputColumns(parseRangeToIndex(`1-${totalColumns - 1}`, totalColumns));
    setOutputColumns(parseRangeToIndex(`${totalColumns}`, totalColumns));
  }, []);
  return (
    <React.Fragment>
      <Grid item xs={12}>
        <Typography item variant="subtitle1" component="h3" sx={{ mb: 0 }}>
          Indicate which columns of the dataset will be used as input and
          output.
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
        defaultValue={`1-${totalColumns - 1}`}
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
        helperText={parseOutputColumnsError ? parseOutputColumnsErrorText : ""}
        defaultValue={totalColumns}
        sx={{ mb: 2 }}
      />
    </React.Fragment>
  );
}

DivideDatasetColumns.propTypes = {
  datasetInfo: PropTypes.shape({
    test_size: PropTypes.number,
    total_columns: PropTypes.number,
    total_rows: PropTypes.number,
    train_size: PropTypes.number,
    val_size: PropTypes.number,
  }),
  inputColumns: PropTypes.arrayOf(PropTypes.number),
  setInputColumns: PropTypes.func.isRequired,
  outputColumns: PropTypes.arrayOf(PropTypes.number),
  setOutputColumns: PropTypes.func.isRequired,
  setColumnsReady: PropTypes.func.isRequired,
};
export default DivideDatasetColumns;
