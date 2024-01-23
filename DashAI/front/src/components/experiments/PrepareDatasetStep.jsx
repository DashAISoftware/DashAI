import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Grid, CircularProgress, Box, Alert, AlertTitle } from "@mui/material";
import DivideDatasetColumns from "./DivideDatasetColumns";
import SplitDatasetRows from "./SplitDatasetRows";
import { getDatasetInfo as getDatasetInfoRequest } from "../../api/datasets";
import { getComponents as getComponentsRequest } from "../../api/component";
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
  const [infoLoading, setInfoLoading] = useState(true);

  // task requirements state
  const [taskRequirements, setTaskRequirements] = useState({
    name: "",
    metadata: {
      inputs_types: [],
      inputs_cardinality: "",
      outputs_types: [],
      outputs_cardinality: "",
    },
  });

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
    train: 70,
    validation: 10,
    test: 20,
  };

  const [rowsPartitionsIndex, setRowsPartitionsIndex] = useState(
    defaultParitionsIndex,
  );
  const [rowsPartitionsPercentage, setRowsPartitionsPercentage] = useState(
    defaultPartitionsPercentage,
  );
  const [isRandom, setIsRandom] = useState(true);
  const [splitsReady, setSplitsReady] = useState(false);

  const getDatasetInfo = async () => {
    setInfoLoading(true);
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
      setInfoLoading(false);
    }
  };

  const getTaskRequirements = async () => {
    try {
      const task = await getComponentsRequest({
        selectTypes: ["Task"],
      });

      setTaskRequirements(
        task.filter((task) => task.name === newExp.task_name)[0],
      );
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the task requirements.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const checkIfSplitsHasChanged = () => {
    if (
      rowsPartitionsPercentage.train !== defaultPartitionsPercentage.train ||
      rowsPartitionsPercentage.test !== defaultPartitionsPercentage.test ||
      rowsPartitionsPercentage.validation !==
        defaultPartitionsPercentage.validation
    ) {
      return true;
    }
    return false;
  };
  useEffect(() => {
    if (columnsReady && splitsReady) {
      setNewExp({
        ...newExp,
        input_columns: inputColumns,
        output_columns: outputColumns,
        splits: !isRandom
          ? { ...rowsPartitionsIndex, is_random: false, has_changed: true }
          : {
              ...rowsPartitionsPercentage,
              is_random: true,
              has_changed: checkIfSplitsHasChanged(),
            },
      }); // splits should depend on preference
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [columnsReady, splitsReady]);

  useEffect(() => {
    getDatasetInfo();
    getTaskRequirements();
  }, []);

  const parseListOfStrings = (stringsList) => {
    return stringsList.join(" or ");
  };
  return (
    <React.Fragment>
      <Alert severity="info" sx={{ mb: 1 }}>
        <AlertTitle>{taskRequirements.name} requirements</AlertTitle>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            The input columns must be of the types{" "}
            {taskRequirements
              ? parseListOfStrings(taskRequirements.metadata.inputs_types)
              : null}
            , and they should have a cardinality of{" "}
            {taskRequirements.metadata.inputs_cardinality}.
          </Grid>
          <Grid item xs={12}>
            The output columns must be of the types{" "}
            {taskRequirements
              ? parseListOfStrings(taskRequirements.metadata.outputs_types)
              : null}
            , and they should have a cardinality of{" "}
            {taskRequirements.metadata.outputs_cardinality}.
          </Grid>
        </Grid>
      </Alert>

      {!infoLoading ? (
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
            isRandom={isRandom}
            setIsRandom={setIsRandom}
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
      has_changed: PropTypes.bool,
      is_random: PropTypes.bool,
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
