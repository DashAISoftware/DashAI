import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Grid } from "@mui/material";
import DivideDatasetColumns from "./DivideDatasetColumns";
import SplitDatasetRows from "./SplitDatasetRows";

/**
 * Step of the experiment modal: Set the input and output columns to use for clasification
 * and the splits for training, validation and testing
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 */
function PrepareDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  // columns index state
  const [inputColumns, setInputColumns] = useState([]);
  const [outputColumns, setOutputColumns] = useState([]);
  const [columnsReady, setColumnsReady] = useState(false);

  const rangeRegex = /^(\d+)(-(\d+))*(,(\d+)(-(\d+))*)*$/;

  // rows index state
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

  const parseRangeToIndex = (value, total) => {
    const numbersArray = [];
    if (!rangeRegex.test(value)) {
      throw new Error("The entered text doesn't fit the example format");
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

  useEffect(() => {
    if (columnsReady && splitsReady) {
      setNewExp({
        ...newExp,
        input_columns: inputColumns,
        output_columns: outputColumns,
        splits:
          rowsPartitionsIndex !== defaultParitionsIndex
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
        <DivideDatasetColumns
          inputColumns={inputColumns}
          setInputColumns={setInputColumns}
          outputColumns={outputColumns}
          setOutputColumns={setOutputColumns}
          setColumnsReady={setColumnsReady}
          parseRangeToIndex={parseRangeToIndex}
        />
        <SplitDatasetRows
          rowsPartitionsIndex={rowsPartitionsIndex}
          setRowsPartitionsIndex={setRowsPartitionsIndex}
          rowsPartitionsPercentage={rowsPartitionsPercentage}
          setRowsPartitionsPercentage={setRowsPartitionsPercentage}
          setSplitsReady={setSplitsReady}
          parseRangeToIndex={parseRangeToIndex}
        />
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
    input_columns: PropTypes.arrayOf(PropTypes.number),
    output_columns: PropTypes.arrayOf(PropTypes.number),
    splits: PropTypes.shape({
      training: PropTypes.number,
      validation: PropTypes.number,
      testing: PropTypes.number,
    }),
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};
export default PrepareDatasetStep;
