import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Grid, CircularProgress, Box } from "@mui/material";
import DivideDatasetColumns from "./DivideDatasetColumns";
import SplitDatasetRows from "./SplitDatasetRows";
import { getDatasetInfo as getDatasetInfoRequest } from "../../api/datasets";
import { useSnackbar } from "notistack";
/**
 * Step of the experiment modal: Set the input and output columns to use for clasification
 * and the splits for training, validation and testing
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 */
function PrepareDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  // dataset info state
  const [datasetInfo, setDatasetInfo] = useState({});
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  // columns index state
  const [inputColumns, setInputColumns] = useState([]);
  const [outputColumns, setOutputColumns] = useState([]);
  const [columnsReady, setColumnsReady] = useState(true);

  const rangeRegex = /^(\d+)(-(\d+))*(,(\d+)(-(\d+))*)*$/;

  // rows index state
  const defaultParitionsIndex = {
    train: [],
    validation: [],
    test: [],
  };
  const defaultPartitionsPercentage = {
    train: 60,
    validation: 20,
    test: 20,
  };

  const [rowsPartitionsIndex, setRowsPartitionsIndex] = useState(
    defaultParitionsIndex,
  );
  const [rowsPartitionsPercentage, setRowsPartitionsPercentage] = useState(
    defaultPartitionsPercentage,
  );
  const [splitsReady, setSplitsReady] = useState(false);

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const datasetInfo = await getDatasetInfoRequest(newExp.dataset.id);
      setDatasetInfo(datasetInfo);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset info.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

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

  // Fetch dataset when the component is mounting
  useEffect(() => {
    getDatasetInfo();
  }, []);
  // Set the input and output columns by default
  useEffect(() => {
    if (!loading) {
      setInputColumns(
        parseRangeToIndex(
          `1-${datasetInfo.total_columns - 1}`,
          datasetInfo.total_columns,
        ),
      );
      setOutputColumns(
        parseRangeToIndex(
          `${datasetInfo.total_columns}`,
          datasetInfo.total_columns,
        ),
      );
    }
  }, [loading]);
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
      {!loading ? (
        <Grid container spacing={1}>
          <DivideDatasetColumns
            datasetInfo={datasetInfo}
            inputColumns={inputColumns}
            setInputColumns={setInputColumns}
            outputColumns={outputColumns}
            setOutputColumns={setOutputColumns}
            setColumnsReady={setColumnsReady}
            parseRangeToIndex={parseRangeToIndex}
          />
          <SplitDatasetRows
            datasetInfo={datasetInfo}
            rowsPartitionsIndex={rowsPartitionsIndex}
            setRowsPartitionsIndex={setRowsPartitionsIndex}
            rowsPartitionsPercentage={rowsPartitionsPercentage}
            setRowsPartitionsPercentage={setRowsPartitionsPercentage}
            setSplitsReady={setSplitsReady}
            parseRangeToIndex={parseRangeToIndex}
          />
        </Grid>
      ) : (
        <Box sx={{ display: "flex" }}>
          <CircularProgress />
        </Box>
      )}
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
