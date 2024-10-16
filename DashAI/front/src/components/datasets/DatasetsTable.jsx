import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import {
  AddCircleOutline as AddIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";
import { Button, Grid, Paper, Typography } from "@mui/material";
import DeleteItemModal from "../custom/DeleteItemModal";
import EditDatasetModal from "./EditDatasetModal";
import DatasetSummaryModal from "./DatasetSummaryModal";
import {
  getDatasets as getDatasetsRequest,
  deleteDataset as deleteDatasetRequest,
} from "../../api/datasets";
import { useSnackbar } from "notistack";
import { formatDate } from "../../utils/index";

function DatasetsTable({
  handleNewDataset,
  updateTableFlag,
  setUpdateTableFlag,
}) {
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState([]);
  const { enqueueSnackbar } = useSnackbar();

  const getDatasets = async () => {
    setLoading(true);
    try {
      const datasets = await getDatasetsRequest();
      setDatasets(datasets);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset table.");
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

  const deleteDataset = async (id) => {
    try {
      await deleteDatasetRequest(id);
      enqueueSnackbar("Dataset successfully deleted.", {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar("Error when trying to delete the dataset");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const createDeleteHandler = React.useCallback(
    (id) => () => {
      deleteDataset(id);
      setUpdateTableFlag(true);
    },
    [],
  );

  // Fetch datasets when the component is mounting
  useEffect(() => {
    getDatasets();
  }, []);

  // triggers an update of the table when updateFlag is set to true
  useEffect(() => {
    if (updateTableFlag) {
      setUpdateTableFlag(false);
      getDatasets();
    }
  }, [updateTableFlag]);

  const columns = React.useMemo(
    () => [
      {
        field: "id",
        headerName: "ID",
        minWidth: 50,
        editable: false,
      },
      {
        field: "name",
        headerName: "Name",
        minWidth: 250,
        editable: false,
      },
      {
        field: "created",
        headerName: "Created",
        minWidth: 140,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "last_modified",
        headerName: "Edited",
        type: Date,
        minWidth: 140,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) => [
          <EditDatasetModal
            key="edit-component"
            name={params.row.name}
            datasetId={params.id}
            updateDatasets={() => setUpdateTableFlag(true)}
          />,
          <DeleteItemModal
            key="delete-component"
            deleteFromTable={createDeleteHandler(params.id)}
          />,
          <DatasetSummaryModal
            key="dataset-summary-component"
            datasetId={params.id}
          />,
        ],
      },
    ],
    [createDeleteHandler],
  );

  return (
    <Paper sx={{ py: 4, px: 6 }}>
      {/* Title and new datasets button */}
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 4 }}
      >
        <Typography variant="h5" component="h2">
          Current datasets
        </Typography>
        <Grid item>
          <Grid container spacing={2}>
            <Grid item>
              <Button
                variant="contained"
                onClick={handleNewDataset}
                endIcon={<AddIcon />}
              >
                New Dataset
              </Button>
            </Grid>
            <Grid item>
              <Button
                variant="contained"
                onClick={() => setUpdateTableFlag(true)}
                endIcon={<UpdateIcon />}
              >
                Update
              </Button>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Datasets Table */}
      <DataGrid
        rows={datasets}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        sortModel={[{ field: "id", sort: "desc" }]}
        pageSize={5}
        pageSizeOptions={[5, 10]}
        disableRowSelectionOnClick
        autoHeight
        loading={loading}
        slots={{
          toolbar: GridToolbar,
        }}
      />
    </Paper>
  );
}

DatasetsTable.propTypes = {
  handleNewDataset: PropTypes.func.isRequired,
  updateTableFlag: PropTypes.bool.isRequired,
  setUpdateTableFlag: PropTypes.func.isRequired,
};

export default DatasetsTable;
