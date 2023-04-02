import React from "react";
import PropTypes from "prop-types";

import { DataGrid, GridActionsCellItem } from "@mui/x-data-grid";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import { Button, Grid, Paper, Typography } from "@mui/material";

function ExperimentsTable({ initialRows, handleNewExperiment }) {
  const [rows, setRows] = React.useState(initialRows);

  const deleteUser = React.useCallback(
    (id) => () => {
      setTimeout(() => {
        setRows((prevRows) => prevRows.filter((row) => row.id !== id));
      });
    },
    []
  );

  const formatDate = (date) => {
    if (date == null) {
      return "";
    }

    const formattedDate =
      date.getDate() + "/" + (date.getMonth() + 1) + "/" + date.getFullYear();

    return formattedDate;
  };

  const columns = React.useMemo(
    () => [
      {
        field: "name",
        headerName: "Name",
        minWidth: 250,
        editable: false,
      },
      {
        field: "taskName",
        headerName: "Task",
        minWidth: 200,
        editable: false,
      },
      {
        field: "dataset",
        headerName: "Dataset",
        minWidth: 200,
        editable: false,
      },
      {
        field: "created",
        headerName: "Created",
        minWidth: 120,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "edited",
        headerName: "Edited",
        type: Date,
        minWidth: 120,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 80,
        getActions: (params) => [
          <GridActionsCellItem
            key="delete-button"
            icon={<DeleteIcon />}
            label="Delete"
            onClick={deleteUser(params.id)}
          />,
        ],
      },
    ],
    [deleteUser]
  );

  return (
    <Paper sx={{ py: 4, px: 6 }}>
      {/* Title and new experiment button */}
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 4 }}
      >
        <Typography variant="h5" component="h2">
          Current experiments
        </Typography>
        <Button
          variant="contained"
          onClick={handleNewExperiment}
          startIcon={<AddIcon />}
        >
          New Experiment
        </Button>
      </Grid>

      {/* Experiments Table */}
      <DataGrid
        rows={rows}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        pageSizeOptions={[10]}
        disableRowSelectionOnClick
        autoHeight
      />
    </Paper>
  );
}

ExperimentsTable.propTypes = {
  initialRows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string))
    .isRequired,
  handleNewExperiment: PropTypes.func,
};

export default ExperimentsTable;
