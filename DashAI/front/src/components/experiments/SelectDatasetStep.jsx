import React, { useState, useEffect } from "react";
import PropTypes, { number } from "prop-types";

import {
  Alert,
  AlertTitle,
  Grid,
  Link,
  Paper,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";
import { Link as RouterLink } from "react-router-dom";

import { getDatasets as getDatasetsRequest } from "../../api/datasets";
import { formatDate } from "../../utils";

const columns = [
  {
    field: "name",
    headerName: "Name",
    minWidth: 250,
    editable: false,
  },
  {
    field: "created",
    headerName: "Created",
    minWidth: 200,
    type: Date,
    valueFormatter: (params) => formatDate(params.value),

    editable: false,
  },
  {
    field: "last_modified",
    headerName: "Last modified",
    minWidth: 200,
    type: Date,
    valueFormatter: (params) => formatDate(params.value),
    editable: false,
  },
];

function SelectDatasetStep({ newExp, setNewExp, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();

  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [datasetsSelected, setDatasetsSelected] = useState([]);
  const [requestError, setRequestError] = useState(false);

  const getDatasets = async () => {
    setLoading(true);
    try {
      const datasets = await getDatasetsRequest();
      setDatasets(datasets);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the datasets list.");
      setRequestError(true);

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
  // fetch datasets when the component is mounting
  useEffect(() => {
    getDatasets();
  }, []);

  // autoselect dataset and enable next button if some dataset was selected previously.
  useEffect(() => {
    if (typeof newExp.dataset === "object" && newExp.dataset !== null) {
      const taskEqualToExpDataset = datasets.map(
        (dataset) => newExp.dataset.id === dataset.id,
      );
      const indexOfTrue = taskEqualToExpDataset.indexOf(true);
      if (indexOfTrue !== -1) {
        setNextEnabled(true);
        setDatasetsSelected([indexOfTrue + 1]);
      }
    } else {
      setDatasetsSelected([]);
    }
  }, [datasets]);

  useEffect(() => {
    if (datasetsSelected.length > 0) {
      // the index of the table start with 1!
      // const dataset = datasets[datasetsSelected[0] - 1];
      const selectedDatasetId = datasetsSelected[0];
      const dataset = datasets.find(
        (dataset) => dataset.id === selectedDatasetId,
      );
      setNewExp({ ...newExp, dataset });
      setNextEnabled(true);
    }
  }, [datasetsSelected]);

  return (
    <React.Fragment>
      {/* Title and new datasets button */}
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 4 }}
      >
        <Typography variant="subtitle1" component="h3">
          Select a dataset for the selected task
        </Typography>
      </Grid>

      {/* Datasets Table */}

      {datasets.length === 0 && !loading && !requestError && (
        <React.Fragment>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <AlertTitle>There is no datasets available.</AlertTitle>
            Go to{" "}
            <Link component={RouterLink} to="/app/data">
              data tab
            </Link>{" "}
            to upload one first.
          </Alert>
          <Typography></Typography>
        </React.Fragment>
      )}
      <Paper>
        <DataGrid
          rows={datasets}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 10,
              },
            },
          }}
          onRowSelectionModelChange={(newRowSelectionModel) => {
            setDatasetsSelected(newRowSelectionModel);
          }}
          rowSelectionModel={datasetsSelected}
          density="compact"
          pageSizeOptions={[10]}
          loading={loading}
          autoHeight
          hideFooterSelectedRowCount
        />
      </Paper>
    </React.Fragment>
  );
}

SelectDatasetStep.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    input_columns: PropTypes.arrayOf(number),
    output_columns: PropTypes.arrayOf(number),
    splits: PropTypes.object,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};
export default SelectDatasetStep;
