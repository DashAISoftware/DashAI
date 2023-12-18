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

  useEffect(() => {
    getDatasetInfo();
  }, []);
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
          />
          <SplitDatasetRows
            datasetInfo={datasetInfo}
            rowsPartitionsIndex={rowsPartitionsIndex}
            setRowsPartitionsIndex={setRowsPartitionsIndex}
            rowsPartitionsPercentage={rowsPartitionsPercentage}
            setRowsPartitionsPercentage={setRowsPartitionsPercentage}
            setSplitsReady={setSplitsReady}
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
