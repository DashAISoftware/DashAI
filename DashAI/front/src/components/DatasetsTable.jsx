import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import AddIcon from "@mui/icons-material/Add";
import { Button, Grid, Paper, Typography } from "@mui/material";
import DeleteDatasetDialog from "./DeleteDatasetDialog";
import EditDatasetModal from "./EditDatasetModal";
import { deleteDataset as deleteDatasetRequest } from "../api/datasets";

function DatasetsTable({ initialRows, handleNewDataset }) {
  const [rows, setRows] = React.useState(initialRows);
  // Keeps internal state (rows) and external state (initialRows) synchronized when external state changes.
  useEffect(() => {
    setRows(initialRows);
  }, [initialRows]);
  const deleteDataset = React.useCallback(
    (id) => () => {
      setTimeout(() => {
        deleteDatasetRequest(id);
        setRows((prevRows) => prevRows.filter((row) => row.id !== id));
      });
    },
    []
  );

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
        field: "task_name",
        headerName: "Task",
        minWidth: 200,
        editable: false,
      },
      {
        field: "file_path",
        headerName: "File Path",
        minWidth: 300,
        editable: false,
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) => [
          <EditDatasetModal key="edit-component" />,
          <DeleteDatasetDialog
            key="delete-component"
            deleteFromTable={deleteDataset(params.id)}
          />,
        ],
      },
    ],
    [deleteDataset]
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
        <Button
          variant="contained"
          onClick={handleNewDataset}
          startIcon={<AddIcon />}
        >
          New Dataset
        </Button>
      </Grid>

      {/* Datasets Table */}
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

DatasetsTable.propTypes = {
  initialRows: PropTypes.arrayOf(
    PropTypes.objectOf(
      PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    )
  ).isRequired,
  handleNewDataset: PropTypes.func,
};

export default DatasetsTable;
