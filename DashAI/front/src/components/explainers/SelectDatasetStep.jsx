import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

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
import { validateDataset as validateDatasetRequest } from "../../api/explainer";
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

export default function SelectDatasetStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState([]);
  const [rowSelectedDataset, setRowSelectedDataset] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(false);
  const [isValidDataset, setIsValidDataset] = useState(false);
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

  // eslint-disable-next-line no-unused-vars
  const validateDataset = async () => {
    try {
      const validation = await validateDatasetRequest(
        newExpl.run_id,
        selectedDatasetId,
      );
      setIsValidDataset(validation.dataset_status === "valid");
      if (validation.dataset_status === "invalid") {
        enqueueSnackbar("The selected dataset is not valid.");
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to validate the selected dataset.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  // fetch datasets when the component is mounting
  useEffect(() => {
    getDatasets();
  }, []);

  useEffect(() => {
    if (rowSelectedDataset.length > 0) {
      const selectedDatasetId = rowSelectedDataset[0];
      const dataset = datasets.find(
        (dataset) => dataset.id === selectedDatasetId,
      );
      setSelectedDatasetId(dataset.id);
    }
  }, [rowSelectedDataset]);

  useEffect(() => {
    if (selectedDatasetId) {
      validateDataset();
    }
  }, [selectedDatasetId]);

  useEffect(() => {
    if (isValidDataset) {
      setNewExpl({ ...newExpl, dataset_id: selectedDatasetId });
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [isValidDataset]);

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
          Select a dataset for the explainer
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
            setRowSelectedDataset(newRowSelectionModel);
          }}
          rowSelectionModel={rowSelectedDataset}
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
  newExpl: PropTypes.shape({
    run_id: PropTypes.string,
    name: PropTypes.string,
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    parameters: PropTypes.object,
    fit_parameters: PropTypes.object,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};
