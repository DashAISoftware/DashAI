import React from "react";
import PropTypes from "prop-types";

import { DataGrid, GridActionsCellItem } from "@mui/x-data-grid";
import DeleteIcon from "@mui/icons-material/Delete";

function ExperimentsTable({ initialRows }) {
  const [rows, setRows] = React.useState(initialRows);

  const deleteUser = React.useCallback(
    (id) => () => {
      setTimeout(() => {
        setRows((prevRows) => prevRows.filter((row) => row.id !== id));
      });
    },
    []
  );

  const columns = React.useMemo(
    () => [
      {
        field: "name",
        headerName: "Name",
        width: 250,
        editable: false,
      },
      {
        field: "taskName",
        headerName: "Task",
        width: 200,
        editable: false,
      },
      {
        field: "dataset",
        headerName: "Dataset",
        width: 200,
        editable: false,
      },
      {
        field: "created",
        headerName: "Created",
        width: 100,
        editable: false,
      },
      {
        field: "edited",
        headerName: "Edited",
        type: Date,
        width: 100,
        editable: false,
      },
      {
        field: "actions",
        type: "actions",
        width: 80,
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
      density="comfortable"
    />
  );
}

ExperimentsTable.propTypes = {
  initialRows: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string))
    .isRequired,
};

export default ExperimentsTable;
