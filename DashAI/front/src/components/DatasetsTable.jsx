import React, { useEffect } from "react";
import PropTypes from "prop-types";

import { DataGrid, GridActionsCellItem } from "@mui/x-data-grid";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import AddIcon from "@mui/icons-material/Add";
import {
  Button,
  Grid,
  Paper,
  Typography,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";

function EditDataset() {
  // const [open, setOpen] = React.useState(false);
  const handleEdit = () => {};
  return (
    <GridActionsCellItem
      key="edit-button"
      icon={<EditIcon />}
      label="Edit"
      onClick={handleEdit}
      sx={{ color: "#f1ae61" }}
    />
  );
}

function DeleteDataset({ deleteFromTable }) {
  const [open, setOpen] = React.useState(false);
  const handleDelete = () => {
    deleteFromTable();
    setOpen(false);
  };
  return (
    <React.Fragment>
      <GridActionsCellItem
        key="delete-button"
        icon={<DeleteIcon />}
        label="Delete"
        onClick={() => setOpen(true)}
        sx={{ color: "#ff8383" }}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <div style={{ backgroundColor: "#2e3037" }}>
          <DialogTitle id="alert-dialog-title">Confirm Deletion</DialogTitle>
          <DialogContent>
            <DialogContentText style={{ color: "#fff" }}>
              Are you sure you want to delete this dataset?
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)} autoFocus>
              Cancel
            </Button>
            <Button onClick={handleDelete}>Delete</Button>
          </DialogActions>
        </div>
      </Dialog>
    </React.Fragment>
  );
}
DeleteDataset.propTypes = {
  deleteFromTable: PropTypes.func.isRequired,
};

function DatasetsTable({ initialRows, handleNewDataset }) {
  const [rows, setRows] = React.useState(initialRows);
  // Keeps internal state (rows) and external state (initialRows) synchronized when external state changes.
  useEffect(() => {
    setRows(initialRows);
  }, [initialRows]);
  const deleteDataset = React.useCallback(
    (id) => () => {
      setTimeout(() => {
        fetch(`${process.env.REACT_APP_DATASET_UPLOAD_ENDPOINT + id}`, {
          method: "DELETE",
        });
        setRows((prevRows) => prevRows.filter((row) => row.id !== id));
      });
    },
    []
  );

  // const formatDate = (date) => {
  //   if (date == null) {
  //     return "";
  //   }

  //   const formattedDate =
  //     date.getDate() + "/" + (date.getMonth() + 1) + "/" + date.getFullYear();

  //   return formattedDate;
  // };

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
      // {
      //   field: "created",
      //   headerName: "Created",
      //   minWidth: 120,
      //   editable: false,
      //   valueFormatter: (params) => formatDate(params.value),
      // },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) => [
          <EditDataset key="edit-component" />,
          <DeleteDataset
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
