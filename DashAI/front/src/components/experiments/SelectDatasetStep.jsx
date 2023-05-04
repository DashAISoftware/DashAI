import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

import { Grid, Paper, Typography } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";

import { getDatasets as getDatasetsRequest } from "../../api/datasets";

const columns = [
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
    minWidth: 200,
    editable: false,
  },
  {
    field: "last_modified",
    headerName: "Last modified",
    minWidth: 200,
    editable: false,
  },
];

function SelectDatasetStep({ setNextEnabled }) {
  const enqueueSnackbar = useSnackbar();

  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rowsSelected, setRowsSelected] = useState([]);

  const getDatasets = async () => {
    setLoading(true);
    try {
      const tasks = await getDatasetsRequest();
      setDatasets(tasks);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the task list.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };
  // Fetch tasks when the component is mounting
  useEffect(() => {
    getDatasets();
  }, []);

  useEffect(() => {
    if (rowsSelected.length > 0) {
      // the index of the table start with 1!
      setSelectedDataset(datasets[rowsSelected[0] - 1]);
      setNextEnabled(true);
    }
  }, [rowsSelected]);

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
          Select a dataset for the selected task
        </Typography>
      </Grid>

      {/* Datasets Table */}
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
          setRowsSelected(newRowSelectionModel);
        }}
        rowSelectionModel={rowsSelected}
        density="compact"
        pageSizeOptions={[10]}
        loading={loading}
        autoHeight
        hideFooterSelectedRowCount
      />
      {JSON.stringify(selectedDataset)}
    </Paper>
  );
}

SelectDatasetStep.propTypes = { setNextEnabled: PropTypes.func.isRequired };

export default SelectDatasetStep;
